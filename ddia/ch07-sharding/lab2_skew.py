# lab2_skew.py - DDIA Ch 7: key-range versus hash sharding, range queries, and hot keys
import hashlib
import random
from collections import Counter

random.seed(7)
SHARDS = 8
h = lambda v: int(hashlib.md5(str(v).encode()).hexdigest(), 16)
show = lambda load: ' '.join(f'{load.get(s, 0):>6}' for s in range(SHARDS))

# 50 sensors each report once a minute. The data covers 8 days; we look at the writes arriving TODAY (day 8).
SENSORS, MINUTES_PER_DAY, DAYS = 50, 1440, 8
today = [(sensor, 7 * MINUTES_PER_DAY + m) for sensor in range(SENSORS) for m in range(MINUTES_PER_DAY)]

print("PART A  where do today's writes land?            shard:" + ''.join(f'{s:>7}' for s in range(SHARDS)))
by_time = Counter(ts // MINUTES_PER_DAY for _, ts in today)                       # key = timestamp, one shard per day
print(f'  key-range sharding on timestamp                      {show(by_time)}   <- one hot shard')
by_hash = Counter(h((sensor, ts)) % SHARDS for sensor, ts in today)               # key = hash of everything
print(f'  hash sharding on (sensor, timestamp)                 {show(by_hash)}')
by_sensor = Counter(sensor * SHARDS // SENSORS for sensor, _ in today)            # key = sensor first, then time
print(f'  key-range sharding on (sensor, timestamp)            {show(by_sensor)}')

print('\nPART B  "readings from sensor 17 over the last 6 hours": how many shards must be asked?')
print('  key-range on timestamp:            1 shard, but it also holds every other sensor for that day')
print(f'  hash on (sensor, timestamp):       {len({h((17, 7 * MINUTES_PER_DAY + m)) % SHARDS for m in range(360)})} shards, the rows are scattered')
print('  key-range on (sensor, timestamp):  1 shard, and the rows sit next to each other')

print('\nPART C  a hot key: one celebrity account receives 30% of all writes')
writes = ['celebrity' if random.random() < 0.30 else f'user{random.randrange(100_000)}' for _ in range(100_000)]
plain = Counter(h(k) % SHARDS for k in writes)
print(f'  hash sharding                                        {show(plain)}   busiest = {max(plain.values()) / (len(writes) / SHARDS):.1f}x fair share')
salted = Counter(h(f'{k}#{random.randrange(16)}' if k == 'celebrity' else k) % SHARDS for k in writes)
print(f'  same, hot key salted with a random 0-15 suffix       {show(salted)}   busiest = {max(salted.values()) / (len(writes) / SHARDS):.1f}x fair share')
print(f'  price: reading the celebrity now means fetching 16 keys from {len({h(f"celebrity#{i}") % SHARDS for i in range(16)})} shards and combining them')
