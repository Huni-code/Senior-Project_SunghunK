"""
Debug: saves HTML of a builtin.com company page to inspect selectors.
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

URL      = "https://builtin.com/company/rocket-companies"
OUT_HTML = Path(__file__).parent.parent / "data" / "debug_builtin.html"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page    = await browser.new_page(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ))
        await page.goto(URL, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)

        html = await page.content()
        OUT_HTML.write_text(html, encoding="utf-8")
        print(f"Saved -> {OUT_HTML}")
        await browser.close()

asyncio.run(main())
