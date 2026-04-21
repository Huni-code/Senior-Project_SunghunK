"""
Phase H1: Collect SIC codes for all CIK-matched companies from SEC submissions API.
Adds sic (TEXT) and sic_description (TEXT) columns to sec_cik_map if missing.
Caches to data/sic_cache.json.
"""
import sqlite3, json, urllib.request, time
from pathlib import Path

DB = 'data/companies.db'
CACHE = 'data/sic_cache.json'
HEADERS = {'User-Agent': 'SeniorProject sunghun.kim@calvin.edu'}


def load_cache():
    if Path(CACHE).exists():
        with open(CACHE) as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE, 'w') as f:
        json.dump(cache, f)


def fetch_sic(cik):
    cik_padded = str(cik).zfill(10)
    url = f'https://data.sec.gov/submissions/CIK{cik_padded}.json'
    req = urllib.request.Request(url, headers=HEADERS)
    data = json.loads(urllib.request.urlopen(req, timeout=15).read())
    return data.get('sic', ''), data.get('sicDescription', '')


def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(sec_cik_map)")
    cols = [r[1] for r in cur.fetchall()]
    if 'sic' not in cols:
        cur.execute('ALTER TABLE sec_cik_map ADD COLUMN sic TEXT')
        print('[DDL] added sic column')
    if 'sic_description' not in cols:
        cur.execute('ALTER TABLE sec_cik_map ADD COLUMN sic_description TEXT')
        print('[DDL] added sic_description column')
    if 'excluded' not in cols:
        cur.execute('ALTER TABLE sec_cik_map ADD COLUMN excluded INTEGER DEFAULT 0')
        print('[DDL] added excluded column')
    if 'exclude_reason' not in cols:
        cur.execute('ALTER TABLE sec_cik_map ADD COLUMN exclude_reason TEXT')
        print('[DDL] added exclude_reason column')
    conn.commit()

    cur.execute('SELECT company_id, cik FROM sec_cik_map ORDER BY cik')
    rows = cur.fetchall()
    print(f'Total CIKs: {len(rows)}')

    cache = load_cache()
    updated = 0
    failed = []

    for i, (cid, cik) in enumerate(rows, 1):
        if cik in cache:
            sic, desc = cache[cik]['sic'], cache[cik]['desc']
        else:
            try:
                sic, desc = fetch_sic(cik)
                cache[cik] = {'sic': sic, 'desc': desc}
                time.sleep(0.12)
            except Exception as e:
                failed.append((cik, str(e)))
                print(f'[FAIL] {cik}: {e}')
                continue

        cur.execute('UPDATE sec_cik_map SET sic = ?, sic_description = ? WHERE company_id = ?',
                    (sic, desc, cid))
        updated += 1
        if i % 50 == 0:
            conn.commit()
            save_cache(cache)
            print(f'  [{i}/{len(rows)}] committed, cache={len(cache)}')

    conn.commit()
    save_cache(cache)
    conn.close()

    print(f'\n=== Phase H1 done ===')
    print(f'Updated: {updated}')
    print(f'Failed: {len(failed)}')
    for cik, err in failed[:10]:
        print(f'  {cik}: {err}')


if __name__ == '__main__':
    main()
