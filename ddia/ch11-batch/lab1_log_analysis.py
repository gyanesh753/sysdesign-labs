# lab1_log_analysis.py - DDIA Ch 11: the five most requested pages in a web log, three ways
import heapq
import itertools
import os
import random
import subprocess
import tempfile
import time
from collections import Counter

random.seed(11)
LINES, PAGES = 400_000, 60_000
weights = [1 / (i + 1) ** 0.9 for i in range(PAGES)]             # a few pages get most of the traffic
urls = random.choices([f'/page/{i}' for i in range(PAGES)], weights, k=LINES)

with tempfile.TemporaryDirectory() as tmp:
    log = os.path.join(tmp, 'access.log')
    with open(log, 'w') as f:
        for i, url in enumerate(urls):
            f.write(f'10.0.{i % 255}.{i % 251} - - [10/Nov/2026:10:{i % 60:02}:00 +0000] "GET {url} HTTP/1.1" 200 {1000 + i % 9000}\n')
    print(f'{LINES:,} log lines, {len(set(urls)):,} distinct pages, {os.path.getsize(log) / 1e6:.0f} MB\n')

    # 1. A chain of small Unix tools, each doing one thing, connected by pipes.
    t = time.perf_counter()
    out = subprocess.run(f"awk '{{print $7}}' {log} | sort | uniq -c | sort -rn | head -5", shell=True, capture_output=True, text=True, env={**os.environ, 'LC_ALL': 'C'}).stdout
    unix = [(line.split()[1], int(line.split()[0])) for line in out.strip().split('\n')]
    unix_s = time.perf_counter() - t

    # 2. One program with an in-memory hash table: one counter per distinct page.
    t = time.perf_counter()
    counts = Counter()
    with open(log) as f:
        for line in f:
            counts[line.split()[6]] += 1
    hashed = counts.most_common(5)
    hash_s = time.perf_counter() - t

    # 3. Sort-based with a fixed memory budget: sort small chunks, write each to disk, then merge the sorted files.
    CHUNK = 50_000
    t = time.perf_counter()
    chunk_files = []
    with open(log) as f:
        while True:
            chunk = sorted(line.split()[6] for line in itertools.islice(f, CHUNK))
            if not chunk:
                break
            path = os.path.join(tmp, f'chunk{len(chunk_files)}')
            with open(path, 'w') as c:
                c.write('\n'.join(chunk) + '\n')
            chunk_files.append(path)
    files = [open(p) for p in chunk_files]
    top = []                                                     # keep only the best five seen so far
    for url, group in itertools.groupby(heapq.merge(*files)):    # identical URLs arrive next to each other
        top = heapq.nlargest(5, top + [(sum(1 for _ in group), url.strip())])
    [f.close() for f in files]
    sort_s = time.perf_counter() - t
    merged = [(url, n) for n, url in top]

    assert dict(unix) == dict(hashed) == dict(merged)
    print(f'{"approach":<44}{"seconds":>8}   what must fit in memory')
    print(f'{"awk | sort | uniq -c | sort -rn | head":<44}{unix_s:>8.2f}   nothing much: sort spills to disk by itself')
    print(f'{"hash table in one program":<44}{hash_s:>8.2f}   one counter per distinct page ({len(counts):,})')
    print(f'{"sort chunks to disk, then merge":<44}{sort_s:>8.2f}   one chunk of {CHUNK:,} lines, whatever the input size ({len(chunk_files)} chunk files)')
    print('\ntop five, identical from all three:')
    for url, n in hashed:
        print(f'  {n:>7,}  {url}')
