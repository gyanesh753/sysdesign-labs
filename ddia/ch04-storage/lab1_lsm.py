# lab1_lsm.py - DDIA Ch 4: a tiny log-structured merge tree: memtable, SSTables, Bloom filters, compaction
import bisect
import random
import time

random.seed(4)


class Bloom:
    """k hash functions over a bit array. Can say 'definitely not here' or 'maybe here'."""

    def __init__(self, keys, bits_per_key=10, k=4):
        self.m = max(8, len(keys) * bits_per_key)
        self.k = k
        self.bits = bytearray(self.m // 8 + 1)
        for key in keys:
            for pos in self._positions(key):
                self.bits[pos >> 3] |= 1 << (pos & 7)

    def _positions(self, key):
        return [hash((seed, key)) % self.m for seed in range(self.k)]

    def might_contain(self, key):
        return all(self.bits[p >> 3] & (1 << (p & 7)) for p in self._positions(key))


class LSM:
    def __init__(self, memtable_limit=2_000, use_bloom=False):
        self.mem, self.limit, self.use_bloom = {}, memtable_limit, use_bloom
        self.sstables = []          # newest first; each is an immutable sorted run
        self.probes = 0             # how many SSTables we had to search (stands in for disk reads)

    def put(self, key, value):
        self.mem[key] = value       # in memory, no disk seek; a real engine also appends to a write-ahead log
        if len(self.mem) >= self.limit:
            self.flush()

    def flush(self):
        keys = sorted(self.mem)
        self.sstables.insert(0, {'keys': keys, 'values': [self.mem[k] for k in keys], 'bloom': Bloom(keys)})
        self.mem = {}

    def get(self, key):
        if key in self.mem:
            return self.mem[key]
        for t in self.sstables:     # newest to oldest: the first hit is the current value
            if self.use_bloom and not t['bloom'].might_contain(key):
                continue
            self.probes += 1
            i = bisect.bisect_left(t['keys'], key)
            if i < len(t['keys']) and t['keys'][i] == key:
                return t['values'][i]
        return None

    def compact(self):
        merged = {}
        for t in reversed(self.sstables):       # oldest first, so newer values overwrite older ones
            merged.update(zip(t['keys'], t['values']))
        keys = sorted(merged)
        self.sstables = [{'keys': keys, 'values': [merged[k] for k in keys], 'bloom': Bloom(keys)}]

    def stored_entries(self):
        return sum(len(t['keys']) for t in self.sstables)


WRITES, KEYSPACE = 200_000, 50_000
db = LSM()
t = time.perf_counter()
for i in range(WRITES):
    db.put(random.randrange(KEYSPACE), i)       # random keys, many overwrites
elapsed = time.perf_counter() - t
live = len({k for t_ in db.sstables for k in t_['keys']} | set(db.mem))
print(f'{WRITES:,} writes in {elapsed:.2f}s  ->  {len(db.sstables)} SSTables')
print(f'entries on "disk": {db.stored_entries():,} for {live:,} live keys  (space amplification {db.stored_entries() / live:.1f}x)')

present = [random.randrange(KEYSPACE) for _ in range(20_000)]
missing = [KEYSPACE + random.randrange(KEYSPACE) for _ in range(20_000)]


def probes_per_read(keys):
    db.probes = 0
    for k in keys:
        db.get(k)
    return db.probes / len(keys)


print('\nSSTables searched per read            existing key   missing key')
print(f'  no Bloom filter, before compaction   {probes_per_read(present):10.1f}   {probes_per_read(missing):10.1f}')
db.use_bloom = True
print(f'  Bloom filter,    before compaction   {probes_per_read(present):10.1f}   {probes_per_read(missing):10.2f}')
t = time.perf_counter()
db.compact()
print(f'  Bloom filter,    after compaction    {probes_per_read(present):10.1f}   {probes_per_read(missing):10.2f}')
print(f'\ncompaction took {time.perf_counter() - t:.2f}s; entries on "disk" now {db.stored_entries():,} (space amplification {db.stored_entries() / live:.1f}x)')
