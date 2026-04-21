"""
Phase H3.5: Name-similarity audit.
Flags CIK mappings where company_name tokens are a strict subset of matched_name tokens,
AND matched_name has extra domain-suspicious tokens (pharma, apparel, energy, etc.).
Outputs CSV for user review.
Runs only on non-excluded rows.
"""
import sqlite3
import re
import csv

DB = 'data/companies.db'
OUT = 'data/phase_h3_name_audit.csv'

SUSPICIOUS_EXTRA_TOKENS = {
    # Pharma/biotech
    'pharmaceuticals', 'pharmaceutical', 'pharma', 'biopharmaceuticals', 'biopharma',
    'biosciences', 'therapeutics', 'bio', 'medicines', 'drug', 'drugs',
    # Consumer goods
    'luggage', 'apparel', 'platinum', 'gold', 'jewelry', 'cosmetics',
    'beverages', 'foods', 'restaurant', 'restaurants',
    # Energy
    'oil', 'gas', 'energy', 'petroleum', 'mining', 'minerals', 'solar',
    # Heavy industry
    'steel', 'aluminum', 'cement', 'chemicals', 'plastics', 'aerospace',
    'aircraft', 'motor', 'motors', 'automotive',
    # Different tech domain than name implies
    'encryption', 'networks', 'networking',
    # Real estate / finance
    'realty', 'reit', 'trust', 'insurance', 'bank',
    # Clearly-different entity type
    'holdings', 'group', 'international', 'corp', 'corporation',  # common but weak signal
}

# Strong signal = suspicious token (pharma/luggage etc.)
STRONG_TOKENS = {
    'pharmaceuticals', 'pharmaceutical', 'pharma', 'biopharmaceuticals', 'biopharma',
    'biosciences', 'therapeutics', 'medicines', 'drug', 'drugs',
    'luggage', 'apparel', 'platinum', 'gold', 'jewelry',
    'oil', 'gas', 'petroleum', 'mining', 'aerospace', 'aircraft',
    'steel', 'aluminum', 'encryption',
    'reit', 'realty', 'insurance',
}


def tokenize(s):
    return set(re.findall(r'[a-z0-9]+', (s or '').lower()))


def is_subset_with_extras(company_tokens, matched_tokens):
    """True if company tokens are fully inside matched_name AND matched has extra tokens."""
    if not company_tokens or not matched_tokens:
        return False
    if not company_tokens.issubset(matched_tokens):
        return False
    extras = matched_tokens - company_tokens
    # Filter noise tokens
    extras = extras - {'inc', 'corp', 'corporation', 'ltd', 'llc', 'plc', 'co',
                       'company', 'the', 'of', 'and', '&', 'de', 'delaware',
                       'holdings'}
    return len(extras) >= 1


def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute('''
        SELECT scm.company_id, cd.name, scm.cik, scm.matched_name, scm.sic, scm.sic_description,
               cc.sector
        FROM sec_cik_map scm
        JOIN companies_deduped cd ON cd.id = scm.company_id
        LEFT JOIN company_classifications cc ON cc.company_id = scm.company_id
        WHERE COALESCE(scm.excluded, 0) = 0
    ''')
    rows = cur.fetchall()
    print(f'Auditing {len(rows)} non-excluded rows')

    flagged = []
    for cid, name, cik, matched, sic, sic_desc, sector in rows:
        c_tokens = tokenize(name)
        m_tokens = tokenize(matched)

        # Skip exact/near-exact matches
        if c_tokens == m_tokens:
            continue

        if not is_subset_with_extras(c_tokens, m_tokens):
            continue

        extras = m_tokens - c_tokens - {'inc', 'corp', 'corporation', 'ltd', 'llc', 'plc',
                                         'co', 'company', 'the', 'of', 'and', 'de',
                                         'delaware', 'holdings'}
        strong_match = extras & STRONG_TOKENS
        severity = 'STRONG' if strong_match else 'REVIEW'

        flagged.append({
            'severity': severity,
            'company_id': cid,
            'company_name': name,
            'matched_name': matched,
            'extra_tokens': ','.join(sorted(extras)),
            'cik': cik,
            'sic': sic or '',
            'sic_description': sic_desc or '',
            'current_sector': sector or '',
        })

    flagged.sort(key=lambda r: (r['severity'] != 'STRONG', r['company_name']))

    with open(OUT, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['severity', 'company_id', 'company_name',
                                           'matched_name', 'extra_tokens', 'cik',
                                           'sic', 'sic_description', 'current_sector'])
        w.writeheader()
        w.writerows(flagged)

    print(f'\nFlagged: {len(flagged)}')
    print(f'  STRONG (auto-drop candidates): {sum(1 for r in flagged if r["severity"] == "STRONG")}')
    print(f'  REVIEW (user decision): {sum(1 for r in flagged if r["severity"] == "REVIEW")}')
    print(f'\nCSV: {OUT}')
    print('\n--- STRONG flags ---')
    for r in flagged:
        if r['severity'] == 'STRONG':
            print(f'  {r["company_name"]:30} -> {r["matched_name"][:50]:50} '
                  f'[{r["extra_tokens"]}]  SIC={r["sic"]}  sector={r["current_sector"]}')


if __name__ == '__main__':
    main()
