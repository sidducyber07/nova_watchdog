import asyncio
import os
import uuid
from pathlib import Path
from playwright.async_api import async_playwright


OUTPUT_DIR = Path(os.getenv("SNAPSHOT_DIR", "./snapshots"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def run_check(url: str, selector: str | None = None, timeout: int = 30000) -> dict:
    """Load a page with Playwright, capture HTML, text and screenshots.

    Returns a dict with paths and data.
    """
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1366, "height": 768})
        page = await context.new_page()
        await page.goto(url, wait_until="networkidle", timeout=timeout)

        html = await page.content()
        text = await page.evaluate("() => document.body.innerText")

        snapshot_id = str(uuid.uuid4())
        snap_dir = OUTPUT_DIR / snapshot_id
        snap_dir.mkdir(parents=True, exist_ok=True)

        # Save HTML
        html_path = snap_dir / "page.html"
        html_path.write_text(html, encoding="utf-8")

        # Save full page screenshot
        full_path = snap_dir / "screenshot.png"
        await page.screenshot(path=str(full_path), full_page=True)

        element_path = None
        if selector:
            try:
                el = await page.query_selector(selector)
                if el:
                    element_path = snap_dir / "element.png"
                    await el.screenshot(path=str(element_path))
            except Exception:
                element_path = None

        await context.close()
        await browser.close()

        return {
            "snapshot_id": snapshot_id,
            "html_path": str(html_path),
            "text": text,
            "screenshot_path": str(full_path),
            "element_path": str(element_path) if element_path else None,
        }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--selector", default=None)
    args = parser.parse_args()

    res = asyncio.run(run_check(args.url, args.selector))
    print(res)
