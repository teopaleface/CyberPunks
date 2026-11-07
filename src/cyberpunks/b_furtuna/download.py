"""Descarcă datele publice ale firului B și verifică sumele de control.

    uv run python -m cyberpunks.b_furtuna.download eaglei --years 2019-2025
    uv run python -m cyberpunks.b_furtuna.download eaglei --meta-only

Fișierele ajung în `data/raw/B/eaglei/` (în afara git). Un fișier deja descărcat, cu md5 corect,
nu se mai descarcă. Descărcarea se reia de unde a rămas (cerere HTTP Range).
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

from cyberpunks.b_furtuna.manifest import EAGLEI_FILES, EAGLEI_META, FIGSHARE, eaglei_year_file
from cyberpunks.common.paths import DATA_RAW

EAGLEI_DIR = DATA_RAW / "B" / "eaglei"
CHUNK = 1 << 20


def md5sum(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(CHUNK * 8), b""):
            h.update(block)
    return h.hexdigest()


def fetch(url: str, dest: Path, size: int, md5: str, retries: int = 5) -> Path:
    """Descarcă `url` în `dest`, cu reluare, apoi verifică mărimea și md5."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size == size and md5sum(dest) == md5:
        print(f"ok (deja descărcat) {dest.name}")
        return dest
    part = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(1, retries + 1):
        have = part.stat().st_size if part.exists() else 0
        headers = {"Range": f"bytes={have}-"} if have else {}
        try:
            with httpx.stream("GET", url, headers=headers, follow_redirects=True, timeout=60) as r:
                if r.status_code == 200 and have:
                    have = 0  # serverul nu acceptă Range: o luăm de la capăt
                elif r.status_code not in (200, 206):
                    raise httpx.HTTPStatusError(f"HTTP {r.status_code}", request=r.request, response=r)
                with open(part, "ab" if have else "wb") as fh:
                    fh.writelines(r.iter_bytes(CHUNK))
            break
        except (httpx.HTTPError, OSError) as exc:
            print(f"încercarea {attempt} a eșuat pentru {dest.name}: {exc}", file=sys.stderr)
            if attempt == retries:
                raise
    got = part.stat().st_size
    if got != size:
        raise RuntimeError(f"{dest.name}: {got} octeți în loc de {size}")
    digest = md5sum(part)
    if digest != md5:
        part.unlink()
        raise RuntimeError(f"{dest.name}: md5 {digest} în loc de {md5}; am șters fișierul, rulează din nou")
    part.rename(dest)
    print(f"ok {dest.name} ({size / 1e6:.0f} MB, md5 verificat)")
    return dest


def eaglei(years: list[int], meta_only: bool = False, workers: int = 3) -> list[Path]:
    names = list(EAGLEI_META) + ([] if meta_only else [eaglei_year_file(y) for y in years])
    jobs = []
    for name in names:
        fid, size, md5 = EAGLEI_FILES[name]
        jobs.append((f"{FIGSHARE}{fid}", EAGLEI_DIR / name, size, md5))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(lambda j: fetch(*j), jobs))


def parse_years(spec: str) -> list[int]:
    if "-" in spec:
        a, b = spec.split("-")
        return list(range(int(a), int(b) + 1))
    return [int(x) for x in spec.split(",")]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dataset", choices=["eaglei"])
    ap.add_argument("--years", default="2019-2025")
    ap.add_argument("--meta-only", action="store_true")
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args(argv)
    if args.dataset == "eaglei":
        eaglei(parse_years(args.years), meta_only=args.meta_only, workers=args.workers)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
