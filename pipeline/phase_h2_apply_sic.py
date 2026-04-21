"""
Phase H2: Apply SIC-based exclusion + reclassification + 7 manual name-collision drops.
Writes directly to DB. Run Phase H3.5 afterward for name-similarity audit.
"""
import sqlite3

DB = 'data/companies.db'

NEW_SECTOR_SEMI = 'Semiconductors'
NEW_SECTOR_HW = 'Hardware & Networking'
MEDTECH_SECTOR = 'GovTech / RegTech / MedTech'

# SIC ranges to exclude (non-tech industries)
EXCLUDE_SIC_EXACT = {
    # Oil/Gas/Mining
    '1000', '1311', '1381', '1623', '2911',
    # Food/Beverage
    '2000', '2015', '2080', '2086',
    # Apparel/Textile/Wood/Paper
    '2273', '2300', '2320', '2430', '2711', '2750', '2780',
    # Chemicals (non-pharma)
    '2800', '2810', '2821', '2840', '2844', '2860', '2870',
    # Plastics/Rubber
    '3021', '3086', '3089',
    # Metals/Steel
    '3312', '3350', '3440', '3490',
    # Industrial machinery (non-computer)
    '3531', '3555', '3559', '3560', '3569',
    # Electrical (non-computer)
    '3613', '3630', '3640', '3651', '3672', '3678', '3679', '3690',
    # Auto/Aerospace
    '3711', '3714', '3721', '3724', '3760', '3812',
    # Instruments (non-medical)
    '3823', '3825', '3826', '3829',
    # Photo/Jewelry/Toys
    '3861', '3911', '3942', '3944', '3949',
    # Transportation
    '4213', '4412', '4512', '4700', '4731',
    # Broadcasting/Utilities
    '4813', '4832', '4833', '4841', '4899', '4911',
    # Wholesale/Retail (except 5961 e-commerce)
    '5000', '5047', '5063', '5099', '5122', '5130',
    '5500', '5600', '5651', '5731', '5812',
    '5900', '5912', '5944', '5945', '5990',
    # REIT/Real Estate
    '6500', '6531', '6770', '6794', '6798',
    # Non-tech services
    '7200', '7320', '7331', '7340', '7381',
    '7600', '7822', '7841', '7900', '7948', '7990',
    # Medical labs/health services
    '8071', '8090',
    # Education/Daycare (non-edtech)
    '8200', '8351',
    # Engineering/Consulting (non-software)
    '8700', '8711', '8731', '8734', '8741', '8742',
}

# Semiconductors — new sector
RECLASSIFY_TO_SEMI = {'3674'}

# Hardware & Networking — new sector
RECLASSIFY_TO_HW = {
    '3570', '3571', '3572', '3573', '3574', '3575', '3576', '3577', '3578', '3579',
    '3661', '3662', '3663', '3669',
}

# Pharma SICs — exclude only if currently in GovTech (per user spec)
PHARMA_SIC = {'2834', '2835', '2836', '2833'}

# Manual name-collision drops (found in prior session)
MANUAL_DROPS = [
    ('Samsara', 'Samsara Luggage'),
    ('Ironclad', 'IRONCLAD ENCRYPTION Corp'),
    ('Karat', 'Karat Platinum, Inc.'),
    ('Iris Software Inc.', 'IRIS INTERNATIONAL INC'),
    ('Epirus', 'EPIRUS Biopharmaceuticals, Inc.'),
    ('ZS', 'ZS Pharma, Inc.'),
    ('Tech Holding', 'Tri-Tech Holding, Inc.'),
]


def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # Ensure new sectors exist (no FK, so just update text)
    # Also need excluded column (added in Phase H1)

    cur.execute('''
        SELECT scm.company_id, cd.name, scm.cik, scm.sic, scm.sic_description, cc.sector
        FROM sec_cik_map scm
        JOIN companies_deduped cd ON cd.id = scm.company_id
        LEFT JOIN company_classifications cc ON cc.company_id = scm.company_id
        WHERE COALESCE(scm.excluded, 0) = 0
    ''')
    rows = cur.fetchall()
    print(f'Processing {len(rows)} active CIK rows')

    actions = {'EXCLUDE_SIC': 0, 'EXCLUDE_PHARMA_MEDTECH': 0,
               'RECLASS_SEMI': 0, 'RECLASS_HW': 0, 'NO_CHANGE': 0}
    excluded_detail = []
    reclassified_detail = []

    for cid, name, cik, sic, sic_desc, sector in rows:
        sic = (sic or '').strip()

        if sic in EXCLUDE_SIC_EXACT:
            cur.execute('UPDATE sec_cik_map SET excluded = 1, exclude_reason = ? WHERE company_id = ?',
                        (f'SIC {sic} {sic_desc}', cid))
            actions['EXCLUDE_SIC'] += 1
            excluded_detail.append((name, sic, sic_desc, sector))
        elif sic in PHARMA_SIC and sector and 'GovTech' in sector:
            cur.execute('UPDATE sec_cik_map SET excluded = 1, exclude_reason = ? WHERE company_id = ?',
                        (f'Pharma/Bio SIC {sic} in MedTech bucket', cid))
            actions['EXCLUDE_PHARMA_MEDTECH'] += 1
            excluded_detail.append((name, sic, sic_desc, sector))
        elif sic in RECLASSIFY_TO_SEMI:
            cur.execute('UPDATE company_classifications SET sector = ? WHERE company_id = ?',
                        (NEW_SECTOR_SEMI, cid))
            actions['RECLASS_SEMI'] += 1
            reclassified_detail.append((name, sic, sector, NEW_SECTOR_SEMI))
        elif sic in RECLASSIFY_TO_HW:
            cur.execute('UPDATE company_classifications SET sector = ? WHERE company_id = ?',
                        (NEW_SECTOR_HW, cid))
            actions['RECLASS_HW'] += 1
            reclassified_detail.append((name, sic, sector, NEW_SECTOR_HW))
        else:
            actions['NO_CHANGE'] += 1

    # Manual drops (name collisions)
    manual_dropped = []
    for name, matched in MANUAL_DROPS:
        cur.execute('''
            UPDATE sec_cik_map
            SET excluded = 1, exclude_reason = ?
            WHERE company_id = (SELECT id FROM companies_deduped WHERE name = ?)
              AND matched_name = ?
        ''', (f'Name collision: mapped to wrong entity ({matched})', name, matched))
        if cur.rowcount > 0:
            manual_dropped.append((name, matched))

    conn.commit()

    print('\n=== Phase H2 results ===')
    for k, v in actions.items():
        print(f'  {k}: {v}')
    print(f'  MANUAL_NAME_COLLISION: {len(manual_dropped)}')

    print('\n--- Reclassified to Semiconductors ---')
    for r in reclassified_detail:
        if r[3] == NEW_SECTOR_SEMI:
            print(f'  {r[0]:40} SIC={r[1]}  {r[2]} -> {r[3]}')
    print('\n--- Reclassified to Hardware & Networking ---')
    for r in reclassified_detail:
        if r[3] == NEW_SECTOR_HW:
            print(f'  {r[0]:40} SIC={r[1]}  {r[2]} -> {r[3]}')
    print('\n--- Manual drops ---')
    for n, m in manual_dropped:
        print(f'  {n} -> {m}')
    print(f'\n--- Excluded (top 30 of {len(excluded_detail)}) ---')
    for name, sic, desc, sec in excluded_detail[:30]:
        print(f'  {name[:40]:40}  SIC={sic}  {(desc or "")[:40]:40}  was: {sec}')

    conn.close()


if __name__ == '__main__':
    main()
