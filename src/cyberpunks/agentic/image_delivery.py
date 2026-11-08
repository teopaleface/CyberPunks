"""Injected transport only. Ledger reserve must atomically persist exact bytes and hash.

Required ledger: reserve(key, png, sha256)->bool; finish(key, status, media_id=None).
Required client: upload(png)->media_id; send_image(recipient, media_id)->None.
authorize() must freshly verify membership, version, recipient and inbound-message
window, using existing MetaTransport.authorize semantics, before each external step.
Keys include report version, recipient and page; unknown outcomes never retry.
"""

from hashlib import sha256


def deliver_images(pages, *, report_id, recipient, ledger, client, authorize):
    results = []
    for page in pages:
        authorize(recipient)
        digest = sha256(page["png"]).hexdigest()
        if digest != page["sha256"]:
            raise ValueError("Page hash mismatch")
        key = (report_id, recipient, page["page"])
        if not ledger.reserve(key, page["png"], digest):
            results.append({"page": page["page"], "status": "already_reserved"})
            continue
        try:
            media_id = client.upload(page["png"])
            authorize(recipient)
            client.send_image(recipient, media_id)
        except Exception:  # noqa: BLE001 - uncertain transport outcomes must remain unreconciled
            ledger.finish(key, "needs_reconciliation")
            results.append({"page": page["page"], "status": "needs_reconciliation"})
        else:
            ledger.finish(key, "sent", media_id=media_id)
            results.append({"page": page["page"], "status": "sent"})
    return results
