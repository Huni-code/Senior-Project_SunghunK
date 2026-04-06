"""
Michigan HQ classifier using Claude Haiku.
Asks whether each company is headquartered in Michigan.

Input:  data/companies_classified.csv
Output: data/companies_michigan.csv  (all companies + is_michigan_hq column)
"""

import csv
import time
from pathlib import Path
import anthropic
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

INPUT_FILE  = Path(__file__).parent.parent / "data" / "companies_classified.csv"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "companies_michigan.csv"


def is_michigan_hq(client, name: str, description: str) -> str:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=5,
        messages=[{
            "role": "user",
            "content": (
                f"Is the company '{name}' headquartered in Michigan, USA? "
                f"Context: {description[:200]}\n"
                "Answer with only 'yes' or 'no'."
            )
        }]
    )
    answer = response.content[0].text.strip().lower()
    return "yes" if "yes" in answer else "no"


def main():
    client = anthropic.Anthropic()

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
    print(f"Classifying {len(remaining)} companies...\n")

    all_fields = list(companies[0].keys()) + ["is_michigan_hq"]
    mode = "a" if done else "w"

    with open(OUTPUT_FILE, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_fields)
        if not done:
            writer.writeheader()

        for i, company in enumerate(remaining, len(done) + 1):
            name        = company["name"]
            description = company.get("description", "")

            print(f"[{i}/{len(companies)}] {name} ...", end=" ", flush=True)

            result = is_michigan_hq(client, name, description)
            print(result.upper())

            writer.writerow({**company, "is_michigan_hq": result})
            f.flush()
            time.sleep(0.2)

    # Summary
    with open(OUTPUT_FILE, encoding="utf-8") as f:
        results = list(csv.DictReader(f))

    michigan = [r for r in results if r["is_michigan_hq"] == "yes"]
    print(f"\nDone! {len(michigan)} Michigan HQ companies out of {len(results)}")
    print(f"Saved -> {OUTPUT_FILE}")

    print("\nMichigan companies:")
    for r in michigan:
        print(f"  {r['name']} | {r['primary_function']} | {r['revenue_model']}")


if __name__ == "__main__":
    main()
