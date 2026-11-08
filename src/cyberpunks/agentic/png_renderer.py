"""Bounded offline Chromium rendering of fixed report templates."""

from hashlib import sha256
from html.parser import HTMLParser


class RendererUnavailable(RuntimeError):
    pass


class _Validator(HTMLParser):
    def handle_starttag(self, tag, attrs):
        if tag not in {
            "html",
            "head",
            "meta",
            "style",
            "body",
            "header",
            "small",
            "h1",
            "p",
            "article",
            "b",
            "br",
            "footer",
        }:
            raise ValueError("Unsupported report element")
        allowed = {"lang", "charset", "http-equiv", "content", "name"}
        if any(k not in allowed for k, _ in attrs):
            raise ValueError("Unsupported report attribute")


def render_pages(html_pages):
    pages = list(html_pages)
    if len(pages) > 250:
        raise ValueError("Too many pages")
    for html in pages:
        if not isinstance(html, str) or len(html.encode()) > 128_000:
            raise ValueError("Report page too large")
        _Validator().feed(html)
    if not pages:
        return []
    from playwright.sync_api import sync_playwright

    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context(
                java_script_enabled=False,
                offline=True,
                service_workers="block",
                viewport={"width": 360, "height": 800},
                device_scale_factor=1,
            )
            context.route("**/*", lambda route: route.abort())
            page = context.new_page()
            page.set_default_timeout(5000)
            for number, html in enumerate(pages, 1):
                page.set_content(html, wait_until="load", timeout=5000)
                box = page.locator("body").bounding_box()
                height = int(box["height"] + 0.999)
                if height < 1 or height > 4096 or box["width"] != 360:
                    raise ValueError("Report dimensions exceed limits")
                page.set_viewport_size({"width": 360, "height": height})
                png = page.screenshot(type="png", clip={"x": 0, "y": 0, "width": 360, "height": height}, timeout=5000)
                if len(png) > 4_000_000:
                    raise ValueError("PNG too large")
                results.append(
                    {"png": png, "width": 360, "height": height, "sha256": sha256(png).hexdigest(), "page": number}
                )
        finally:
            browser.close()
    return results
