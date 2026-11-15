# lab2_column_compression.py - DDIA Ch 4: why column storage compresses so well, and why sort order matters
import os
import tempfile
import time

import duckdb
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

N = 500_000
rng = np.random.default_rng(4)
df = pd.DataFrame({
    'order_id': np.arange(N),
    'day': rng.integers(0, 365, N),
    'country': rng.choice(['IN', 'US', 'AE', 'DE', 'BR', 'JP'], N),
    'product_id': rng.integers(0, 500, N),
    'qty': rng.integers(1, 5, N),
    'price': rng.uniform(5, 500, N).round(2),
})


def runs(values):
    """Number of runs a run-length encoder would store: 1 + the number of places the value changes."""
    v = np.asarray(values)
    return 1 + int((v[1:] != v[:-1]).sum())


by_country_day = df.sort_values(['country', 'day']).reset_index(drop=True)
print('Run-length encoding: how many (value, count) pairs does a column need?')
print(f'{"column":<12}{"distinct":>10}{"runs, arrival order":>22}{"runs, sorted by country,day":>30}')
for col in ['country', 'day', 'product_id']:
    print(f'{col:<12}{df[col].nunique():>10}{runs(df[col]):>22,}{runs(by_country_day[col]):>30,}')

with tempfile.TemporaryDirectory() as tmp:
    path = lambda name: os.path.join(tmp, name)
    df.to_csv(path('rows.csv'), index=False)
    pq.write_table(pa.Table.from_pandas(df), path('plain.parquet'), compression='none', use_dictionary=False)
    pq.write_table(pa.Table.from_pandas(df), path('encoded.parquet'), compression='none')
    pq.write_table(pa.Table.from_pandas(by_country_day), path('sorted.parquet'), compression='none')
    pq.write_table(pa.Table.from_pandas(by_country_day), path('sorted_zstd.parquet'), compression='zstd')

    print('\nFile sizes for the same 500,000 rows')
    for name, label in [('rows.csv', 'CSV, row by row'), ('plain.parquet', 'columns, no encoding'), ('encoded.parquet', 'columns, dictionary + run-length'),
                        ('sorted.parquet', 'same, sorted by country, day'), ('sorted_zstd.parquet', 'same, plus zstd compression')]:
        print(f'  {label:<36}{os.path.getsize(path(name)) / 1e6:7.2f} MB')

    meta = pq.ParquetFile(path('sorted.parquet')).metadata
    print('\nBytes per column in the sorted file')
    for c in range(meta.num_columns):
        size = sum(meta.row_group(g).column(c).total_compressed_size for g in range(meta.num_row_groups))
        print(f'  {meta.schema.column(c).name:<12}{size / 1e3:9.1f} kB')

    query = "SELECT country, SUM(qty * price) FROM '{}' GROUP BY country"
    print('\nOne aggregate that needs 3 of the 6 columns')
    for name in ['rows.csv', 'sorted.parquet']:
        t = time.perf_counter()
        duckdb.sql(query.format(path(name))).fetchall()
        print(f'  from {name:<16}{(time.perf_counter() - t) * 1000:7.1f} ms')
