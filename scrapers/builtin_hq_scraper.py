"""
Built In Michigan HQ Scraper
Visits each company's builtin.com detail page and extracts HQ location.
Filters for Michigan-headquartered companies only.

Input:  data/companies_classified.csv  (has builtin_url column)
Output: data/companies_hq.csv          (Michigan HQ only, with hq_city + hq_state added)
"""

import asyncio
import csv
import random
from pathlib import Path
from playwright.async_api import async_playwright

INPUT_FILE  = Path(__file__).parent.parent / "data" / "companies_classified.csv"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "companies_hq.csv"

MICHIGAN_KEYWORDS = ["michigan", "detroit", "ann arbor", "grand rapids",
                     "lansing", "kalamazoo", "troy", "flint", "sterling heights",
                     "dearborn", "livonia", "warren", "farmington", "okemos",
                     "northville", "novi", "southfield", "auburn hills"]


def is_michigan(location: str) -> bool:
    loc = location.lower()
    return any(kw in loc for kw in MICHIGAN_KEYWORDS)


async def get_hq(page, url: str) -> str:
    """Visit company detail page and return HQ location string."""
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(random.randint(1500, 2500))

        hq = await page.evaluate("""
            () => {
                // Primary: HQ location div on builtin.com company pages
                const el = document.querySelector(
                    'div.ms-sm.font-barlow.fw-medium.fs-md.text-gray-04'
                );
                if (el) return el.innerText.trim();
                return '';
            }
        """)
        return hq.strip()

    except Exception as e:
        print(f"  [error] {url}: {e}")
        return ""


async def main():
    with open(INPUT_FILE, encoding="utf-8") as f:
        companies = list(csv.DictReader(f))
    print(f"Loaded {len(companies)} companies")

    # Resume support
    done = set()
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                done.add(row["name"])
        print(f"Resuming — {len(done)} already done.")

    remaining = [c for c in companies if c["name"] not in done]
    print(f"Processing {len(remaining)} companies...\n")

    base_fields = list(companies[0].keys())
    all_fields  = base_fields + ["hq_raw", "hq_michigan"]

    mode = "a" if done else "w"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()

        with open(OUTPUT_FILE, mode, newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=all_fields)
            if not done:
                writer.writeheader()

            for i, company in enumerate(remaining, len(done) + 1):
                name = company["name"]
                url  = company.get("builtin_url", "")

                print(f"[{i}/{len(companies)}] {name} ...", end=" ", flush=True)

                if not url:
                    print("no URL, skipping")
                    writer.writerow({**company, "hq_raw": "", "hq_michigan": "no"})
                    f.flush()
                    continue

                hq = await get_hq(page, url)
                michigan = "yes" if is_michigan(hq) else "no"

                print(f"{michigan.upper()} | {hq[:60]}")

                writer.writerow({**company, "hq_raw": hq, "hq_michigan": michigan})
                f.flush()

                await asyncio.sleep(random.uniform(1.5, 3.0))

        await browser.close()

    # Summary
    with open(OUTPUT_FILE, encoding="utf-8") as f:
        results = list(csv.DictReader(f))

    michigan_cos = [r for r in results if r["hq_michigan"] == "yes"]
    print(f"\nDone! {len(michigan_cos)} Michigan HQ companies out of {len(results)}")
    print(f"Saved -> {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
