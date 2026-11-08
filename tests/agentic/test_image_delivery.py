from hashlib import sha256

import pytest

from cyberpunks.agentic.image_delivery import deliver_images


@pytest.mark.parametrize("failure", [None, "upload", "send"])
def test_callbacks_timeout_and_pages(failure):
    reserved, statuses, calls = {}, {}, []

    class Ledger:
        def reserve(self, key, png, digest):
            if key in reserved:
                return False
            reserved[key] = (png, digest)
            return True

        def finish(self, key, status, media_id=None):
            statuses[key] = status

    class Client:
        def upload(self, png):
            calls.append("upload")
            if failure == "upload":
                raise TimeoutError()
            return "media"

        def send_image(self, recipient, media):
            calls.append("send")
            if failure == "send":
                raise TimeoutError()

    pages = [{"png": b"png", "sha256": sha256(b"png").hexdigest(), "page": i} for i in (1, 2)]

    def authorize(recipient):
        assert recipient == "verified"
        calls.append("authorize")

    kwargs = {
        "report_id": "v1",
        "recipient": "verified",
        "ledger": Ledger(),
        "client": Client(),
        "authorize": authorize,
    }
    result = deliver_images(pages, **kwargs)
    assert [r["status"] for r in result] == ["sent" if failure is None else "needs_reconciliation"] * 2
    assert len(reserved) == 2
    before = calls.count("upload")
    assert all(r["status"] == "already_reserved" for r in deliver_images(pages, **kwargs))
    assert calls.count("upload") == before
    assert calls[:2] == ["authorize", "upload"]
