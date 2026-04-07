"""
Built In US Tech Company Scraper
Scrapes builtin.com/companies/{hub} for major US tech hubs.
Output: data/companies_raw.csv

Features:
- Appends per hub as scraped (checkpoint-safe)
- Skips already-completed hubs on restart
- Max 300 companies per hub
"""

import asyncio
import csv
import random
import sys
from pathlib import Path
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

TECH_HUBS = [
    "new-york-city",
    "chicago",
    "los-angeles",
    "san-francisco",
    "seattle",
    "boston",
    "austin",
    "denver",
    "atlanta",
    "dallas",
    "washington-dc",
    "miami",
    "philadelphia",
    "raleigh",
    "minneapolis",
    "portland",
    "nashville",
    "san-diego",
    "michigan",
]

HUB_LOCATION_MAP = {
    "new-york-city": "new-york-city",
    "chicago": "chicago",
    "los-angeles": "los-angeles",
    "san-francisco": "san-francisco",
    "seattle": "seattle",
    "boston": "boston",
    "austin": "austin",
    "denver": "denver",
    "atlanta": "na/usa/ga/atlanta",
    "dallas": "dallas",
    "washington-dc": "na/usa/dc/washington",
    "miami": "na/usa/fl/miami",
    "philadelphia": "na/usa/pa/philadelphia",
    "raleigh": "raleigh",
    "minneapolis": "minneapolis",
    "portland": "na/usa/or/portland",
    "nashville": "na/usa/tn/nashville",
    "san-diego": "na/usa/ca/san-diego",
    "michigan": "michigan",
}

HUB_LIMIT = 400

OUTPUT_FILE = Path(__file__).parent.parent / "data" / "companies_raw.csv"
FIELDS = ["name", "builtin_url", "sectors", "location", "employees", "description", "hub"]


def load_existing() -> set[str]:
    """Returns completed_hubs from existing CSV (hubs with >= HUB_LIMIT entries)."""
    completed_hubs: set[str] = set()

    if not OUTPUT_FILE.exists():
        return completed_hubs

    with open(OUTPUT_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        hub_counts: dict[str, int] = {}
        for row in reader:
            hub = row["hub"]
            hub_counts[hub] = hub_counts.get(hub, 0) + 1

    for hub, count in hub_counts.items():
        if count >= HUB_LIMIT:
            completed_hubs.add(hub)
            print(f"  [skip] {hub} — already has {count} companies")

    return completed_hubs


def make_url(hub: str, page_num: int) -> str:
    slug = HUB_LOCATION_MAP.get(hub, hub)
    base = f"https://builtin.com/companies/location/{slug}"
    return base if page_num == 1 else f"{base}?page={page_num}"


async def scrape_page(page, hub: str, page_num: int) -> list[dict]:
    url = make_url(hub, page_num)
    await page.goto(url, wait_until="networkidle", timeout=60000)
    try:
        await page.wait_for_selector(
            ".company-card-horizontal:not(.placeholder-wave)", timeout=30000
        )
    except Exception:
        print(f"  [{hub}] page {page_num} timed out, treating as empty")
        return []

    companies = await page.evaluate("""
        () => {
            const cards = document.querySelectorAll('.company-card-horizontal:not(.placeholder-wave)');
            return Array.from(cards).map(card => {
                const h2      = card.querySelector('h2');
                const overlay = card.querySelector('a.company-card-overlay');
                const secEl   = card.querySelector('.company-info-section .text-gray-04');
                const spans   = card.querySelectorAll('.company-stats-grid span.text-gray-03');
                const descEl  = card.querySelector('.company-tagline-4-rows p');

                return {
                    name:        h2      ? h2.innerText.trim() : '',
                    builtin_url: overlay ? overlay.href : '',
                    sectors:     secEl   ? secEl.innerText.trim() : '',
                    location:    spans[0] ? spans[0].innerText.trim() : '',
                    employees:   spans[1] ? spans[1].innerText.trim() : '',
                    description: descEl  ? descEl.innerText.trim() : '',
                };
            }).filter(c => c.name);
        }
    """)

    for c in companies:
        c["hub"] = hub
        c["name"] = c["name"].replace("\u2014", "-")
        c["description"] = c["description"].replace("\u2014", "-")

    return companies


async def has_next_page(page, current_page: int) -> bool:
    btn = await page.query_selector(f'a[href*="page={current_page + 1}"]')
    return btn is not None


async def scrape_hub(browser, hub: str, needs_header: list[bool]):
    context = await browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    )
    page = await context.new_page()
    hub_total = 0
    page_num = 1
    seen_this_hub: set[str] = set()  # dedup within this hub only

    while hub_total < HUB_LIMIT:
        print(f"  [{hub}] page {page_num}...", end=" ", flush=True)
        companies = await scrape_page(page, hub, page_num)
        print(f"{len(companies)} found on page")

        if not companies:
            print(f"  [{hub}] no companies found, stopping")
            break

        new_companies = []
        for c in companies:
            if c["builtin_url"] not in seen_this_hub and hub_total + len(new_companies) < HUB_LIMIT:
                seen_this_hub.add(c["builtin_url"])
                new_companies.append(c)

        if new_companies:
            append_to_csv(new_companies, write_header=needs_header[0])
            needs_header[0] = False
            hub_total += len(new_companies)
            print(f"  [{hub}] +{len(new_companies)} written (hub total: {hub_total})")

        if hub_total >= HUB_LIMIT:
            print(f"  [{hub}] hit limit of {HUB_LIMIT}")
            break

        if not await has_next_page(page, page_num):
            break

        page_num += 1
        await asyncio.sleep(random.uniform(2.0, 4.0))

    await context.close()
    print(f"  [{hub}] done — {hub_total} companies saved")


def append_to_csv(companies: list[dict], write_header: bool):
    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerows(companies)


async def main():
    OUTPUT_FILE.parent.mkdir(exist_ok=True)

    completed_hubs = load_existing()
    needs_header = [not OUTPUT_FILE.exists() or OUTPUT_FILE.stat().st_size == 0]

    print(f"Resuming: {len(completed_hubs)} hubs already done\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        for hub in TECH_HUBS:
            if hub in completed_hubs:
                continue

            print(f"\nScraping hub: {hub}")
            try:
                await scrape_hub(browser, hub, needs_header)
            except Exception as e:
                print(f"  [{hub}] ERROR: {e}")

            await asyncio.sleep(random.uniform(3.0, 6.0))

        await browser.close()

    print(f"\nDone! All hubs scraped.")


if __name__ == "__main__":
    asyncio.run(main())
