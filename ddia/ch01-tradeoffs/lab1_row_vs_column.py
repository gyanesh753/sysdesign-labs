# lab1_row_vs_column.py - DDIA Ch 1: same data, row store (SQLite) vs column store (DuckDB)
import os
import sqlite3
import time

import duckdb
import numpy as np
import pandas as pd

N = 2_000_000
rng = np.random.default_rng(42)
df = pd.DataFrame({
    'order_id': np.arange(N),
    'user_id': rng.integers(0, 200_000, N),
    'country': rng.choice(['IN', 'US', 'AE', 'DE', 'BR', 'JP'], N),
    'qty': rng.integers(1, 5, N),
    'price': rng.uniform(5, 500, N).round(2),
    'ts': pd.Timestamp('2026-01-01') + pd.to_timedelta(rng.integers(0, 300 * 86400, N), unit='s'),
})

# Row store: SQLite
sq = sqlite3.connect('orders.db')
df.to_sql('orders', sq, if_exists='replace', index=False, chunksize=100_000)
sq.execute('CREATE INDEX IF NOT EXISTS idx_order_id ON orders(order_id)')
sq.commit()

# Column store: DuckDB
dk = duckdb.connect('orders.duckdb')
dk.execute('CREATE OR REPLACE TABLE orders AS SELECT * FROM df')


def timeit(label, fn):
    t = time.perf_counter()
    fn()
    print(f'{label:<34}{time.perf_counter() - t:8.3f}s')


ids = rng.integers(0, N, 5_000).tolist()

# OLTP-style: 5,000 point lookups by key
timeit('SQLite  point lookups', lambda: [sq.execute('SELECT * FROM orders WHERE order_id=?', (i,)).fetchone() for i in ids])
timeit('DuckDB  point lookups', lambda: [dk.execute('SELECT * FROM orders WHERE order_id=?', [i]).fetchone() for i in ids])

# OLAP-style: one aggregate over every row
q = 'SELECT country, SUM(qty*price) AS revenue FROM orders GROUP BY country'
timeit('SQLite  group-by aggregate', lambda: sq.execute(q).fetchall())
timeit('DuckDB  group-by aggregate', lambda: dk.execute(q).fetchall())

print()
for f in ('orders.db', 'orders.duckdb'):
    print(f'{f:<16}{os.path.getsize(f) / 1e6:8.1f} MB')
