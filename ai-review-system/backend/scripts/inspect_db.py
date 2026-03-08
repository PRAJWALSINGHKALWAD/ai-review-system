import sqlite3
import json
import os

DB_PATH = 'reviews.db'

if not os.path.exists(DB_PATH):
    print('DB file not found:', DB_PATH)
    raise SystemExit(1)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

for table in ('reviews','responses'):
    try:
        cur.execute(f"SELECT * FROM {table}")
        rows = [dict(r) for r in cur.fetchall()]
        print(f"--- {table} ({len(rows)} rows) ---")
        print(json.dumps(rows, default=str, indent=2))
    except Exception as e:
        print(f"ERROR reading {table}: {e}")

conn.close()
