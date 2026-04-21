"""
Phase H5: Add 30 public tech big-names missing from builtin.com scrape,
plus un-exclude Netflix (legacy SIC 7841 Video Tape Rental -> genuine streaming subscription).
Follows ai_additions.py pattern: strict match via company_tickers.json.
"""
import sqlite3, json, urllib.request
from pathlib import Path

DB = 'data/companies.db'
TICKERS_CACHE = 'data/company_tickers.json'
HEADERS = {'User-Agent': 'SeniorProject sunghun.kim@calvin.edu'}

ADDITIONS = [
    # (company_name, ticker, sector, revenue_model, reason)

    # Semiconductors — fill INSUF sector
    ('Intel', 'INTC', 'Semiconductors', 'Licensing (enterprise software)', 'CPU, chip manufacturing'),
    ('AMD', 'AMD', 'Semiconductors', 'Licensing (enterprise software)', 'CPU/GPU, AI accelerators'),
    ('Broadcom', 'AVGO', 'Semiconductors', 'Licensing (enterprise software)', 'Networking chips, AI ASICs'),
    ('Qualcomm', 'QCOM', 'Semiconductors', 'Licensing (enterprise software)', 'Mobile chips, wireless IP'),
    ('Texas Instruments', 'TXN', 'Semiconductors', 'Licensing (enterprise software)', 'Analog, embedded chips'),
    ('Applied Materials', 'AMAT', 'Semiconductors', 'Licensing (enterprise software)', 'Semi equipment'),
    ('Lam Research', 'LRCX', 'Semiconductors', 'Licensing (enterprise software)', 'Semi equipment'),
    ('KLA', 'KLAC', 'Semiconductors', 'Licensing (enterprise software)', 'Semi equipment/metrology'),
    ('Marvell Technology', 'MRVL', 'Semiconductors', 'Licensing (enterprise software)', 'Data infra chips'),
    ('Analog Devices', 'ADI', 'Semiconductors', 'Licensing (enterprise software)', 'Analog/signal chips'),

    # Hardware & Networking
    ('Cisco', 'CSCO', 'Hardware & Networking', 'Licensing (enterprise software)', 'Networking equipment'),
    ('HP Inc', 'HPQ', 'Hardware & Networking', 'Licensing (enterprise software)', 'PCs, printers'),
    ('Hewlett Packard Enterprise', 'HPE', 'Hardware & Networking', 'Licensing (enterprise software)', 'Servers, edge compute'),
    ('Juniper Networks', 'JNPR', 'Hardware & Networking', 'Licensing (enterprise software)', 'Networking equipment'),
    ('NetApp', 'NTAP', 'Hardware & Networking', 'Licensing (enterprise software)', 'Enterprise storage'),
    ('Arista Networks', 'ANET', 'Hardware & Networking', 'Licensing (enterprise software)', 'Cloud networking'),

    # Enterprise/ERP/HRM — megacaps missing
    ('Oracle', 'ORCL', 'Enterprise / ERP / HRM', 'Licensing (enterprise software)', 'Database, ERP, cloud infra'),
    ('SAP', 'SAP', 'Enterprise / ERP / HRM', 'Licensing (enterprise software)', 'ERP, enterprise apps'),
    ('IBM', 'IBM', 'Enterprise / ERP / HRM', 'Licensing (enterprise software)', 'Enterprise software, consulting, hybrid cloud'),

    # Gaming
    ('Electronic Arts', 'EA', 'Gaming & virtual environments', 'Transaction fees / marketplace cut', 'Game publisher'),
    ('Roblox', 'RBLX', 'Gaming & virtual environments', 'Transaction fees / marketplace cut', 'UGC gaming platform'),

    # Creative & design tools
    ('Autodesk', 'ADSK', 'Creative & design tools', 'Subscription (SaaS)', 'CAD, 3D design SaaS'),
    ('Ansys', 'ANSS', 'Creative & design tools', 'Subscription (SaaS)', 'Simulation software'),
    ('PTC', 'PTC', 'Creative & design tools', 'Subscription (SaaS)', 'CAD/PLM software'),

    # Subscription content
    ('Spotify', 'SPOT', 'Subscription content', 'Subscription (SaaS)', 'Music streaming'),
    ('Warner Bros Discovery', 'WBD', 'Subscription content', 'Subscription (SaaS)', 'Media, streaming (HBO Max)'),

    # E-learning
    ('Coursera', 'COUR', 'E-learning & skill platforms', 'Subscription (SaaS)', 'Online courses'),
    ('Chegg', 'CHGG', 'E-learning & skill platforms', 'Subscription (SaaS)', 'Student learning svcs'),

    # Productivity
    ('Zoom Video Communications', 'ZM', 'Productivity & collaboration', 'Subscription (SaaS)', 'Video meetings'),
    ('Asana', 'ASAN', 'Productivity & collaboration', 'Subscription (SaaS)', 'Project management'),
]


def load_tickers():
    if Path(TICKERS_CACHE).exists():
        with open(TICKERS_CACHE) as f:
            return json.load(f)
    url = 'https://www.sec.gov/files/company_tickers.json'
    req = urllib.request.Request(url, headers=HEADERS)
    data = json.loads(urllib.request.urlopen(req).read())
    with open(TICKERS_CACHE, 'w') as f:
        json.dump(data, f)
    return data


def find_cik(ticker, tickers_data):
    t = ticker.upper()
    for _, entry in tickers_data.items():
        if entry['ticker'].upper() == t:
            return str(entry['cik_str']).zfill(10), entry['title']
    return None, None


def main():
    tickers = load_tickers()
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # Un-exclude Netflix (SIC 7841 Video Tape Rental is legacy misclassification)
    cur.execute('''UPDATE sec_cik_map
                   SET excluded = 0,
                       exclude_reason = 'SIC 7841 legacy (Video Tape Rental) restored: genuine streaming subscription content'
                   WHERE company_id = (SELECT id FROM companies_deduped WHERE name = 'Netflix')''')
    print(f'[NETFLIX-RESTORE] rowcount={cur.rowcount}')

    added = []
    missing = []

    for name, ticker, sector, revmodel, reason in ADDITIONS:
        cur.execute('SELECT id FROM companies_deduped WHERE LOWER(name) = LOWER(?)', (name,))
        row = cur.fetchone()
        if row:
            company_id = row[0]
            print(f'[SKIP-EXISTS] {name} id={company_id}')
        else:
            cur.execute('''INSERT INTO companies_deduped (name, hub, state, company_size, employees_count)
                           VALUES (?, ?, ?, ?, ?)''', (name, 'Unknown', 'Unknown', 'Large', None))
            company_id = cur.lastrowid
            # Ensure id column synced with rowid (legacy schema quirk from ai_additions)
            cur.execute('UPDATE companies_deduped SET id = ? WHERE rowid = ? AND id IS NULL',
                        (company_id, company_id))
            print(f'[INSERT] {name} -> id={company_id}')

        cik, title = find_cik(ticker, tickers)
        if not cik:
            missing.append((name, ticker))
            print(f'  [NO-CIK] {ticker}')
            continue

        cur.execute('SELECT cik FROM sec_cik_map WHERE company_id = ?', (company_id,))
        existing = cur.fetchone()
        if existing:
            if existing[0] != cik:
                cur.execute('UPDATE sec_cik_map SET cik = ?, matched_name = ?, excluded = 0 WHERE company_id = ?',
                            (cik, title, company_id))
                print(f'  [CIK-UPDATE] {existing[0]} -> {cik} ({title})')
            else:
                cur.execute('UPDATE sec_cik_map SET excluded = 0 WHERE company_id = ?', (company_id,))
                print(f'  [CIK-OK] {cik} ({title})')
        else:
            cur.execute('INSERT INTO sec_cik_map (company_id, cik, matched_name) VALUES (?, ?, ?)',
                        (company_id, cik, title))
            print(f'  [CIK-INSERT] {cik} ({title})')

        cur.execute('SELECT sector FROM company_classifications WHERE company_id = ?', (company_id,))
        cls = cur.fetchone()
        if cls:
            cur.execute('UPDATE company_classifications SET sector = ?, revenue_model = ? WHERE company_id = ?',
                        (sector, revmodel, company_id))
            print(f'  [CLASS-UPDATE] {cls[0]} -> {sector}')
        else:
            cur.execute('INSERT INTO company_classifications (company_id, sector, revenue_model) VALUES (?, ?, ?)',
                        (company_id, sector, revmodel))
            print(f'  [CLASS-INSERT] {sector}')

        added.append((company_id, cik, name))

    conn.commit()
    conn.close()

    print(f'\n=== Summary ===')
    print(f'Added/updated: {len(added)}')
    print(f'Missing CIK: {len(missing)}')
    for n, t in missing:
        print(f'  {n} ({t})')


if __name__ == '__main__':
    main()
