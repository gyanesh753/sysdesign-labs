# lab1_rebalancing.py - DDIA Ch 7: add one node to a 10-node cluster. How much data has to move?
import bisect
import hashlib
from collections import Counter

KEYS = [f'user:{i}' for i in range(100_000)]


def h(value):
    return int(hashlib.md5(str(value).encode()).hexdigest(), 16)


def moved(before, after):
    return sum(1 for k in KEYS if before[k] != after[k]) / len(KEYS)


def spread(assignment):
    load = Counter(assignment.values())
    return max(load.values()) / (len(KEYS) / len(load))          # busiest node relative to a perfectly even share


print(f'{"scheme":<40}{"keys moved":>12}{"ideal":>8}{"busiest node vs even share":>30}')

# 1. hash(key) mod N: the node is baked into the formula, so changing N reshuffles almost everything
mod = lambda n: {k: h(k) % n for k in KEYS}
a, b = mod(10), mod(11)
print(f'{"hash mod N":<40}{moved(a, b):>12.1%}{1 / 11:>8.1%}{spread(b):>29.2f}x')

# 2. fixed number of shards: key -> one of 1,024 shards forever; only whole shards change owner
SHARDS = 1024
owner10 = {s: s % 10 for s in range(SHARDS)}
owner11 = dict(owner10)
want = SHARDS // 11
taken = Counter()
for s in range(SHARDS):                                           # the new node takes a fair share from every old node
    if sum(taken.values()) < want and taken[owner10[s]] < want // 10 + 1:
        taken[owner10[s]] += 1
        owner11[s] = 10
fixed = lambda owner: {k: owner[h(k) % SHARDS] for k in KEYS}
a, b = fixed(owner10), fixed(owner11)
print(f'{"fixed 1,024 shards, reassign whole shards":<40}{moved(a, b):>12.1%}{1 / 11:>8.1%}{spread(b):>29.2f}x')


# 3. consistent hashing: nodes sit at points on a ring; a key belongs to the next point clockwise
def ring(nodes, points_per_node):
    points = sorted((h(f'{n}#{i}'), n) for n in range(nodes) for i in range(points_per_node))
    positions = [p for p, _ in points]
    return {k: points[bisect.bisect(positions, h(k)) % len(points)][1] for k in KEYS}


for points in [1, 200]:
    a, b = ring(10, points), ring(11, points)
    print(f'{f"consistent hashing, {points} point(s) per node":<40}{moved(a, b):>12.1%}{1 / 11:>8.1%}{spread(b):>29.2f}x')
