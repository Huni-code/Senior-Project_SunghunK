"""
LLM-based company classifier using Claude Haiku.
Classifies each company by:
  - revenue_model
  - work_regime
  - primary_function  (Media / Tool / Bureaucracy)
  - secondary_function

Input:  data/companies_filtered.csv
Output: data/companies_classified.csv
"""

import csv
import json
import time
from pathlib import Path
import anthropic
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

INPUT_FILE  = Path(__file__).parent.parent / "data" / "companies_michigan_raw.csv"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "companies_classified.csv"

NEW_FIELDS = ["revenue_model", "work_regime", "primary_function", "secondary_function"]

SYSTEM_PROMPT = """
You are an expert analyst classifying Michigan tech companies for an academic research project.

You will be given a company's name, description, and sector tags.
Classify the company using EXACTLY these frameworks:

---

REVENUE MODEL (pick one):
- Subscription: recurring payments for access (SaaS, streaming)
- Advertising: revenue from showing ads to users
- Transaction fees: takes a cut of each transaction or marketplace sale
- Usage-based: charges per API call, compute hour, or unit consumed
- Licensing: one-time or annual license for software or IP
- Services: consulting, implementation, professional services
- Hardware sales: physical product revenue
- Mixed: clearly combines 2 or more of the above

---

WORK REGIME (pick one):
- Startup/Venture: VC-backed, fast growth, equity-driven culture
- Corporate Agile: large company using agile or scrum methods
- Open Source: community-driven development model
- Government/Public Sector: serves or operates like public institutions
- Outsourcing: primarily delivers services for other companies

---

PRIMARY FUNCTION (pick one) + SECONDARY FUNCTION (pick one or None):
- Media: delivers content, information, or entertainment to users
- Tool: extends human or team capability and productivity
- Bureaucracy: digitizes administration, compliance, governance, audit

Examples:
- Google Search -> Primary: Media, Secondary: Bureaucracy
- GitHub -> Primary: Tool, Secondary: Bureaucracy
- Okta -> Primary: Bureaucracy, Secondary: None
- Stripe -> Primary: Bureaucracy, Secondary: Tool

---

Return ONLY valid JSON, no explanation:
{
  "revenue_model": "...",
  "work_regime": "...",
  "primary_function": "...",
  "secondary_function": "..."
}
"""


def make_user_prompt(name: str, description: str, sectors: str) -> str:
    return f"Company: {name}\nSectors: {sectors}\nDescription: {description}\n\nClassify this company."


def classify_company(client: anthropic.Anthropic, name: str, description: str, sectors: str) -> dict:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": make_user_prompt(name, description, sectors)
        }]
    )

    raw = response.content[0].text.strip()

    # Strip markdown code blocks if present (```json ... ``` or ``` ... ```)
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print(f"  [warn] JSON parse failed for {name}: {raw[:80]}")
        return {field: "unknown" for field in NEW_FIELDS}


def main():
    client = anthropic.Anthropic()

    with open(INPUT_FILE, encoding="utf-8") as f:
        companies = list(csv.DictReader(f))
    print(f"Loaded {len(companies)} companies from {INPUT_FILE.name}")

    # Resume support — skip already-done companies
    done = set()
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                done.add(row["name"])
        print(f"Resuming — {len(done)} already classified.")

    remaining = [c for c in companies if c["name"] not in done]
    print(f"Classifying {len(remaining)} companies...\n")

    base_fields = list(companies[0].keys())
    all_fields  = base_fields + NEW_FIELDS

    mode = "a" if done else "w"
    with open(OUTPUT_FILE, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_fields)
        if not done:
            writer.writeheader()

        for i, company in enumerate(remaining, len(done) + 1):
            name        = company["name"]
            description = company.get("description", "")
            sectors     = company.get("sectors", "")

            print(f"[{i}/{len(companies)}] {name} ...", end=" ", flush=True)

            result = classify_company(client, name, description, sectors)

            row = {**company, **{field: result.get(field, "unknown") for field in NEW_FIELDS}}
            writer.writerow(row)
            f.flush()

            print(f"{result.get('primary_function','?')} | {result.get('revenue_model','?')}")

            time.sleep(0.3)  # avoid rate limit

    print(f"\nDone! -> {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
