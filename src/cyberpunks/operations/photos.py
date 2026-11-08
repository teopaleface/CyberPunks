"""Bounded raster decoding and private SQLite photo records. No user filenames or paths."""

from __future__ import annotations

import json
import warnings
from datetime import timedelta
from io import BytesIO
from uuid import UUID

from PIL import Image, ImageOps, UnidentifiedImageError

from cyberpunks.operations.models import OperationError

MAX_BYTES = 5 * 1024 * 1024
MAX_PIXELS = 12_000_000
MAX_DIMENSION = 10_000
PENDING_QUOTA = 20
DRAFT_TTL = timedelta(hours=24)
GC_BATCH_SIZE = 20
FORMATS = {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}

# Unknown command/expiry states fail closed. A confirmed reference is evidence,
# even if an inconsistent photo row still says draft.
PROTECTED_REFERENCE = """EXISTS (
 SELECT 1 FROM proposal_photos pp JOIN proposals p ON p.proposal_id=pp.proposal_id
 LEFT JOIN commands c ON c.command_id=p.command_id
 WHERE pp.photo_id=photos.photo_id AND (
  (p.command_id IS NOT NULL AND (c.status IS NULL OR c.status!='cancelled')) OR
  (p.command_id IS NULL AND (
   julianday(json_extract(p.body,'$.expires_at')) IS NULL OR
   julianday(json_extract(p.body,'$.expires_at'))>julianday(:current_time)
  ))
 )
)"""
EXPIRED_DRAFT = f"""status='draft' AND command_id IS NULL AND
 COALESCE(julianday(json_extract(body,'$.created_at'))<=julianday(:cutoff),0) AND NOT {PROTECTED_REFERENCE}"""


def expiry_params(organization_id, scenario, at):
    return {
        "organization_id": organization_id,
        "scenario": scenario,
        "current_time": at.isoformat(),
        "cutoff": (at - DRAFT_TTL).isoformat(),
    }


def collect_expired(db, organization_id, scenario, at):
    """Bounded, transactional cleanup on uploads only; no reads start a cleanup."""
    rows = db.execute(
        f"SELECT photo_id FROM photos WHERE organization_id=:organization_id AND scenario=:scenario "
        f"AND {EXPIRED_DRAFT} ORDER BY rowid LIMIT :batch_size",
        {**expiry_params(organization_id, scenario, at), "batch_size": GC_BATCH_SIZE},
    ).fetchall()
    for row in rows:
        # Only expired proposals / cancelled commands can remain referenced here.
        db.execute("DELETE FROM proposal_photos WHERE photo_id=?", (row["photo_id"],))
        db.execute("DELETE FROM photos WHERE photo_id=?", (row["photo_id"],))


def pending_count(db, organization_id, scenario, uploader_id, actor_signature, work_ids, at):
    # Expired rows outside this request's cleanup batch must not block uploads.
    return db.execute(
        f"SELECT count(*) FROM photos WHERE organization_id=:organization_id AND scenario=:scenario "
        f"AND uploader_id=:uploader_id AND actor_signature=:actor_signature "
        f"AND work_item_id IN (SELECT value FROM json_each(:work_ids)) "
        f"AND status='draft' AND NOT ({EXPIRED_DRAFT})",
        {
            **expiry_params(organization_id, scenario, at),
            "uploader_id": uploader_id,
            "actor_signature": actor_signature,
            "work_ids": json.dumps(work_ids),
        },
    ).fetchone()[0]


def is_expired(db, pid, at):
    return (
        db.execute(
            f"SELECT 1 FROM photos WHERE photo_id=:photo_id AND {EXPIRED_DRAFT}",
            {"photo_id": pid, "current_time": at.isoformat(), "cutoff": (at - DRAFT_TTL).isoformat()},
        ).fetchone()
        is not None
    )


def error(code="invalid_photo", message="The photo is unavailable or no longer valid for this finding.", status=409):
    raise OperationError(status, code, message)


def photo_id(value: str) -> str:
    try:
        return str(UUID(value))
    except ValueError:
        error("not_found", "Photo not found in your scope.", 404)


class BoundedOutput(BytesIO):
    def write(self, content):
        if self.tell() + len(content) > MAX_BYTES:
            error("photo_too_large", "The processed photo exceeds 5 MiB.", 413)
        return super().write(content)


def sanitize(content: bytes, mime_type: str) -> tuple[bytes, int, int]:
    if mime_type not in FORMATS:
        error("invalid_photo_type", "Upload a JPEG, PNG or WebP raster image.", 415)
    if len(content) > MAX_BYTES:
        error("photo_too_large", "Photos must not exceed 5 MiB.", 413)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(content)) as image:
                width, height = image.size
                if image.format != FORMATS[mime_type]:
                    error("invalid_photo_type", "The decoded image must match its Content-Type.", 415)
                if width * height > MAX_PIXELS or max(width, height) > MAX_DIMENSION:
                    error("photo_dimensions", "The photo exceeds the supported image dimensions.", 413)
                if getattr(image, "n_frames", 1) != 1:
                    error("invalid_photo_type", "Upload a single still image.", 415)
                image.verify()
            with Image.open(BytesIO(content)) as image:
                image.load()
                image = ImageOps.exif_transpose(image)
                mode = "RGBA" if mime_type != "image/jpeg" and "A" in image.getbands() else "RGB"
                # A new raster has no EXIF, comments, ICC, XMP, or other source metadata.
                clean = Image.new(mode, image.size)
                clean.paste(image.convert(mode))
                output = BoundedOutput()
                clean.save(output, format=FORMATS[mime_type], **({"quality": 85} if mime_type != "image/png" else {}))
                return output.getvalue(), clean.width, clean.height
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        SyntaxError,
        EOFError,
        OverflowError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        error("invalid_photo", "The image could not be safely decoded.", 422)


def validate_refs(db, organization_id, uploader_id, scenario, work_item_id, ids, actor_signature, *, at, frozen=None):
    """Use inside the caller's transaction at prepare, confirm and final attachment."""
    metadata = []
    for pid in ids:
        row = db.execute(
            "SELECT * FROM photos WHERE photo_id=? AND organization_id=? AND scenario=? AND work_item_id=?",
            (pid, organization_id, scenario, work_item_id),
        ).fetchone()
        if (
            not row
            or row["status"] != "draft"
            or row["uploader_id"] != uploader_id
            or row["actor_signature"] != actor_signature
            or is_expired(db, pid, at)
        ):
            error()
        metadata.append(json.loads(row["body"]))
    if frozen is not None and metadata != frozen:
        error()
    return metadata
