# lab3_secondary_indexes.py - DDIA Ch 7: local versus global secondary indexes on sharded data
import hashlib
import random

import numpy as np

random.seed(7)
rng = np.random.default_rng(7)
SHARDS, CARS = 8, 40_000
COLORS = ['red', 'blue', 'black', 'white', 'silver', 'green']
MAKES = ['Tata', 'Toyota', 'Honda', 'Ford', 'BMW']
h = lambda v: int(hashlib.md5(str(v).encode()).hexdigest(), 16)
cars = {i: {'color': random.choice(COLORS), 'make': random.choice(MAKES)} for i in range(CARS)}

# LOCAL index: each shard indexes only its own cars.  GLOBAL index: one index over all cars, itself sharded by the indexed value.
local = [{} for _ in range(SHARDS)]
global_ = [{} for _ in range(SHARDS)]
for car_id, car in cars.items():
    for field in ('color', 'make'):
        term = f'{field}:{car[field]}'
        local[h(car_id) % SHARDS].setdefault(term, set()).add(car_id)
        global_[h(term) % SHARDS].setdefault(term, set()).add(car_id)

term = 'color:red'
from_local = set().union(*(shard.get(term, set()) for shard in local))            # must ask every shard
from_global = global_[h(term) % SHARDS][term]                                     # one index shard knows them all
assert from_local == from_global
print(f'query "{term}": {len(from_local):,} cars either way\n')

print(f'{"":<18}{"index shards asked per query":>30}{"shards written per insert":>28}')
print(f'{"local index":<18}{SHARDS:>30}{1:>28}')
writes = np.mean([len({h(i) % SHARDS} | {h(f"{f}:{c[f]}") % SHARDS for f in ("color", "make")}) for i, c in cars.items()])
print(f'{"global index":<18}{1:>30}{writes:>28.2f}   (the data shard plus one index shard per indexed field)')

# Latency: every shard request takes a random time; a scatter-gather query waits for the slowest reply.
one = rng.lognormal(np.log(5), 0.6, 100_000)
scatter = rng.lognormal(np.log(5), 0.6, (100_000, SHARDS)).max(axis=1)
p = lambda x: np.percentile(x, [50, 99])
print('\nlatency of the index lookup itself (ms)         p50      p99')
print(f'  global index, 1 request                   {p(one)[0]:7.1f}  {p(one)[1]:7.1f}')
print(f'  local index, wait for all {SHARDS} shards         {p(scatter)[0]:7.1f}  {p(scatter)[1]:7.1f}')
print('\nBut a global index spans shards: updating the car and its index entries is not one atomic write,')
print('so the index is usually updated asynchronously and can briefly miss a car that was just added.')
