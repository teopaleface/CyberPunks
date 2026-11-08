"""Bounded offline Chromium PDF rendering of the same fixed, validated report templates.

The input is exactly what ``report_templates.render_report`` produces. Every page is validated by the
same element/attribute allow-list as the PNG renderer, then folded into one document with fixed
constant markup of our own. JavaScript, network and service workers stay blocked in the sandbox.
"""

from __future__ import annotations

import re
from hashlib import sha256

from .png_renderer import RendererUnavailable, _Validator  # noqa: F401 - shared allow-list and error type

MAX_PAGES = 250
MAX_PAGE_HTML = 128_000
MAX_PDF_BYTES = 8_000_000
PDF_MIME = "application/pdf"
TITLE = "PPC Daybreak report"

# Fixed constants: A4 print layout for the 360 px phone templates. Cards never split across pages.
# The source footer ("Pagina N din M" of the template page) is replaced by a Chromium footer that
# carries the physical page number and total, so the numbers are right however a card flows.
_PRINT_CSS = (
    "<style>@page{size:A4;margin:12mm 12mm 17mm}"
    "body{width:auto!important;padding:0!important;margin:0!important;font-size:12px!important}"
    "section{break-after:page;break-inside:auto}section:last-child{break-after:auto}"
    "h1{font-size:20px!important;margin:4px 0}header>p{font-size:12px!important}"
    "p{line-height:1.25!important;margin:4px 0!important}"
    "article{break-inside:avoid;padding:8px 14px!important;margin:8px 0!important}"
    "article>p:first-child{margin-top:0!important}"
    "header{break-after:avoid;padding-bottom:2px}footer{display:none!important}</style>"
)
CONFIRMATION = "Confirmarea se face în aplicația autentificată."
_FOOTER = (
    '<div style="width:100%;box-sizing:border-box;padding:0 12mm;font:9px Arial,sans-serif;color:#555">'
    'Pagina <span class="pageNumber"></span> din <span class="totalPages"></span>. ' + CONFIRMATION + "</div>"
)
_NO_HEADER = '<div style="font-size:0"></div>'

_HEAD = re.compile(r"<head>(.*?)</head>", re.DOTALL)
_BODY = re.compile(r"<body>(.*)</body>\s*</html>\s*$", re.DOTALL)


def _fold(pages: list[str]) -> str:
    """Fold validated template pages into one document. Page chrome comes from the first page's head."""
    sections = []
    for html in pages:
        body = _BODY.search(html)
        if html.count("<body>") != 1 or html.count("</body>") != 1 or not body:
            raise ValueError("Unexpected report page structure")
        sections.append("<section>" + body.group(1) + "</section>")
    head = _HEAD.search(pages[0])
    if not head:
        raise ValueError("Unexpected report page structure")
    return (
        '<!doctype html><html lang="ro"><head>'
        + head.group(1)
        + f"<title>{TITLE}</title>"
        + _PRINT_CSS
        + "</head><body>"
        + "".join(sections)
        + "</body></html>"
    )


def render_pdf(html_pages) -> dict:
    """Return ``{"pdf", "sha256", "bytes", "page_count", "source_pages"}`` for the folded report."""
    pages = list(html_pages)
    if not pages:
        raise ValueError("No report pages")
    if len(pages) > MAX_PAGES:
        raise ValueError("Too many pages")
    for html in pages:
        if not isinstance(html, str) or len(html.encode()) > MAX_PAGE_HTML:
            raise ValueError("Report page too large")
        _Validator().feed(html)
    document = _fold(pages)
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context(java_script_enabled=False, offline=True, service_workers="block")
            context.route("**/*", lambda route: route.abort())
            page = context.new_page()
            page.set_default_timeout(10_000)
            page.set_content(document, wait_until="load", timeout=10_000)
            pdf = page.pdf(
                prefer_css_page_size=True,
                print_background=True,
                display_header_footer=True,
                header_template=_NO_HEADER,
                footer_template=_FOOTER,
            )
        finally:
            browser.close()
    return describe_pdf(pdf, source_pages=len(pages))


def describe_pdf(pdf: bytes, *, source_pages: int | None = None) -> dict:
    """Check the structural envelope of a PDF and compute its identity. Raises ValueError otherwise."""
    if not isinstance(pdf, (bytes, bytearray)) or not pdf.startswith(b"%PDF-") or b"%%EOF" not in pdf[-1100:]:
        raise ValueError("Not a complete PDF")
    if len(pdf) > MAX_PDF_BYTES:
        raise ValueError("PDF too large")
    pdf = bytes(pdf)
    count = len(re.findall(rb"/Type\s*/Page(?![s\w])", pdf))
    if count < 1:
        raise ValueError("PDF has no pages")
    return {
        "pdf": pdf,
        "sha256": sha256(pdf).hexdigest(),
        "bytes": len(pdf),
        "page_count": count,
        "source_pages": source_pages if source_pages is not None else count,
    }
