# lab2_quorums.py - DDIA Ch 6: leaderless replication: when do w acknowledgements and r responses guarantee a fresh read?
import random

random.seed(6)
TRIALS = 20_000


def stale_read_rate(n, w, r, down=0):
    """One client writes version 2 over version 1 and stops as soon as w nodes acknowledge.
    Another client then reads from r nodes and takes the newest version it sees."""
    stale = unavailable = 0
    for _ in range(TRIALS):
        alive = random.sample(range(n), n - down)
        if len(alive) < w or len(alive) < r:
            unavailable += 1
            continue
        nodes = [1] * n
        for i in random.sample(alive, w):             # the w nodes that happened to answer first
            nodes[i] = 2
        if max(nodes[i] for i in random.sample(alive, r)) < 2:
            stale += 1
    done = TRIALS - unavailable
    return (stale / done if done else float('nan')), unavailable / TRIALS


print('PART A  n = 5 replicas, all healthy: chance that a read misses the latest write')
print('         ' + ''.join(f'r={r:<7}' for r in range(1, 6)))
for w in range(1, 6):
    cells = []
    for r in range(1, 6):
        rate, _ = stale_read_rate(5, w, r)
        cells.append(f'{rate:6.1%}{"*" if w + r > 5 else " "} ')
    print(f'  w={w}   ' + ''.join(cells))
print('  * marks w + r > n: the write set and the read set must overlap in at least one node')

print('\nPART B  n = 5, w = 3, r = 3: how many nodes can be down?')
for down in range(0, 4):
    rate, unavailable = stale_read_rate(5, 3, 3, down)
    status = 'requests fail: not enough nodes for a quorum' if unavailable == 1 else f'works, stale reads {rate:.1%}'
    print(f'  {down} down: {status}')

print('\nPART C  read repair: a stale replica is fixed by the reads that notice it')
nodes = [2, 2, 2, 1, 1]                               # two replicas missed the write
reads = 0
while min(nodes) < 2:
    reads += 1
    sample = random.sample(range(5), 3)
    newest = max(nodes[i] for i in sample)
    for i in sample:
        nodes[i] = newest                             # write the newest value back to the replicas that were behind
print(f'  all five replicas up to date after {reads} reads; a key nobody reads would stay stale without a background process')
