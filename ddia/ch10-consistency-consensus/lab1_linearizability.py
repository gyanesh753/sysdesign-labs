# lab1_linearizability.py - DDIA Ch 10: is this history of reads and writes something a single copy of the data could produce?
import random

random.seed(10)


def linearizable(history, initial=0):
    """history: list of (kind, value, start, end). Try to place every operation at one instant inside its
    start..end interval so that each read returns the latest write before it. Brute-force search."""
    ops = sorted(history, key=lambda o: o[2])

    def search(remaining, current):
        if not remaining:
            return True
        earliest_end = min(o[3] for o in remaining)
        for o in remaining:
            if o[2] > earliest_end:                 # o started after another pending operation finished: it cannot go first
                continue
            kind, value = o[0], o[1]
            if kind == 'read' and value != current:
                continue
            rest = [x for x in remaining if x is not o]
            if search(rest, value if kind == 'write' else current):
                return True
        return False

    return search(ops, initial)


print('PART A  two small histories (the write of 1 takes from t=2 to t=8)')
ok = [('write', 1, 2, 8), ('read', 0, 1, 3), ('read', 1, 4, 6), ('read', 1, 7, 9)]
bad = [('write', 1, 2, 8), ('read', 1, 3, 5), ('read', 0, 6, 7)]
print(f'  reads see 0, then 1, then 1                      -> linearizable: {linearizable(ok)}')
print(f'  one read sees 1, a LATER read sees 0 again       -> linearizable: {linearizable(bad)}')
print('  The second history is what a lagging replica produces: the value appears to go back in time.')


def simulate(read_from, lag):
    """One leader, one asynchronous follower. A writer increments the value; two readers read."""
    history, pending, leader, follower, t = [], [], 0, 0, 0.0
    for _ in range(6):
        t += random.uniform(0.5, 2)
        for when, v in [p for p in pending if p[0] <= t]:
            follower = v
        pending = [p for p in pending if p[0] > t]
        if random.random() < 0.4:
            leader += 1
            history.append(('write', leader, t, t + 0.3))
            pending.append((t + 0.3 + random.uniform(0, lag), leader))
        else:
            source = leader if read_from == 'leader' else follower
            history.append(('read', source, t, t + 0.3))
        t += 0.3
    return history


print('\nPART B  2,000 random histories from a leader with one asynchronous follower')
print(f'  {"reads served by":<28}{"histories that are NOT linearizable":>38}')
for read_from, lag in [('leader', 5), ('follower, lag up to 1', 1), ('follower, lag up to 5', 5)]:
    source = 'leader' if read_from == 'leader' else 'follower'
    bad_count = sum(not linearizable(simulate(source, lag)) for _ in range(2_000))
    print(f'  {read_from:<28}{bad_count / 2_000:>37.1%}')
