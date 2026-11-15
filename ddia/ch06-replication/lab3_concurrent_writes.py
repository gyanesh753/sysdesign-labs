# lab3_concurrent_writes.py - DDIA Ch 6: concurrent writes: last write wins, version vectors, and a CRDT counter
import random

random.seed(6)
REPLICAS, CLICKS = 3, 300

# A "like" counter. Each replica accepts clicks locally while offline from the others, then they sync.

print('PART A  last write wins (each replica stores a value and a timestamp; highest timestamp survives)')
lww = [(0, 0.0)] * REPLICAS
clock = 0.0
for _ in range(CLICKS):
    r = random.randrange(REPLICAS)
    clock += random.random()
    lww[r] = (lww[r][0] + 1, clock)                   # read local value, add one, stamp it
winner = max(lww, key=lambda v: v[1])
print(f'  {CLICKS} clicks happened, the merged counter says {winner[0]}  ->  {CLICKS - winner[0]} clicks silently discarded')

print('\nPART B  version vectors: detect that two values are concurrent instead of pretending one is newer')


def compare(a, b):
    if a == b:
        return 'equal'
    if all(x <= y for x, y in zip(a, b)):
        return 'a happened before b: b can safely overwrite a'
    if all(x >= y for x, y in zip(a, b)):
        return 'b happened before a: a can safely overwrite b'
    return 'CONCURRENT: neither knew about the other, keep both and merge'


base = [1, 0, 0]                                       # written at replica 0
edit_at_1 = [1, 1, 0]                                  # replica 1 saw base, then wrote
edit_at_2 = [1, 0, 1]                                  # replica 2 saw base, then wrote, without seeing replica 1's edit
later = [1, 1, 1]                                      # someone merged both, then wrote
for name, a, b in [('base vs edit at replica 1', base, edit_at_1), ('edit at 1 vs edit at 2', edit_at_1, edit_at_2), ('edit at 2 vs merged', edit_at_2, later)]:
    print(f'  {name:<28}{str(a):>10} {str(b):<10} {compare(a, b)}')

print('\nPART C  a CRDT counter: each replica counts only its own clicks; merging takes the maximum per replica')
crdt = [[0] * REPLICAS for _ in range(REPLICAS)]       # crdt[r] is replica r's view: one slot per replica
random.seed(6)
for step in range(CLICKS):
    r = random.randrange(REPLICAS)
    crdt[r][r] += 1
    if step % 37 == 0:                                 # occasional sync between two random replicas, in any order
        a, b = random.sample(range(REPLICAS), 2)
        merged = [max(x, y) for x, y in zip(crdt[a], crdt[b])]
        crdt[a], crdt[b] = merged[:], merged[:]
print(f'  before final sync, replicas report {[sum(v) for v in crdt]}')
final = [max(col) for col in zip(*crdt)]
orders = []
for _ in range(5):                                     # merge in several random orders: the answer must not depend on it
    views = [v[:] for v in crdt]
    random.shuffle(views)
    acc = views[0]
    for v in views[1:]:
        acc = [max(x, y) for x, y in zip(acc, v)]
    orders.append(sum(acc))
print(f'  after merging in 5 different orders: {orders}  ->  every click counted, same answer every time')
assert set(orders) == {CLICKS} and sum(final) == CLICKS
