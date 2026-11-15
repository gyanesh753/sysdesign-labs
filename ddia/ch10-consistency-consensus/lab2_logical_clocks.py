# lab2_logical_clocks.py - DDIA Ch 10: ordering events without trusting the wall clock
import random

random.seed(10)
NODES, STEPS = 3, 4_000
SKEW_MS = [0, -40, 25]                                  # each node's wall clock is off by this much

lamport = [0] * NODES
vector = [[0] * NODES for _ in range(NODES)]
hlc = [(0, 0)] * NODES                                  # hybrid logical clock: (wall-clock part, counter)
events, in_flight, bad_wall = [], [], 0
now = 0.0


def hlc_tick(node, wall, received=None):
    last_wall, counter = hlc[node]
    top = max(wall, last_wall, received[0] if received else 0)
    if top == last_wall and received and top == received[0]:
        counter = max(counter, received[1]) + 1
    elif top == last_wall:
        counter += 1
    elif received and top == received[0]:
        counter = received[1] + 1
    else:
        counter = 0
    hlc[node] = (top, counter)
    return hlc[node]


for _ in range(STEPS):
    now += random.expovariate(1 / 5)                    # about 5 ms between events
    node = random.randrange(NODES)
    wall = int(now + SKEW_MS[node])
    due = [m for m in in_flight if m['to'] == node and m['arrives'] <= now]
    if due:                                             # receive a message
        m = due[0]
        in_flight.remove(m)
        lamport[node] = max(lamport[node], m['lamport']) + 1
        vector[node] = [max(a, b) for a, b in zip(vector[node], m['vector'])]
        vector[node][node] += 1
        stamp = hlc_tick(node, wall, m['hlc'])
        if wall <= m['wall']:
            bad_wall += 1                               # the wall clock claims the message arrived before it was sent
        assert lamport[node] > m['lamport'] and stamp > m['hlc']
    else:
        lamport[node] += 1
        vector[node][node] += 1
        stamp = hlc_tick(node, wall)
        if random.random() < 0.08:                      # now and then, send a message to another node
            to = random.choice([n for n in range(NODES) if n != node])
            in_flight.append({'to': to, 'arrives': now + random.uniform(1, 20), 'lamport': lamport[node],
                              'vector': vector[node][:], 'hlc': stamp, 'wall': wall})
    events.append({'node': node, 'lamport': (lamport[node], node), 'vector': vector[node][:], 'hlc': stamp, 'true': now})

print(f'{len(events):,} events on {NODES} nodes whose wall clocks are off by {SKEW_MS} ms\n')
print('PART A  does the timestamp of a received message come after the timestamp of sending it?')
print(f'  wall clock:        violated {bad_wall} times (an effect stamped earlier than its cause)')
print('  Lamport timestamp: never violated (checked on every receive)')
print('  hybrid clock:      never violated (checked on every receive)')

print('\nPART B  Lamport timestamps give one total order, with the node number breaking ties')
ordered = sorted(events, key=lambda e: e['lamport'])
assert len({e['lamport'] for e in events}) == len(events)
print(f'  every one of the {len(events):,} events has a distinct (counter, node) pair; first three: {[e["lamport"] for e in ordered[:3]]}')

print('\nPART C  what a single number cannot tell you')


def happened_before(a, b):
    return all(x <= y for x, y in zip(a, b)) and a != b


sample = random.sample(events, 400)
pairs = [(a, b) for i, a in enumerate(sample) for b in sample[i + 1:]]
concurrent = sum(1 for a, b in pairs if not happened_before(a['vector'], b['vector']) and not happened_before(b['vector'], a['vector']))
print(f'  of {len(pairs):,} pairs of events, vector clocks show {concurrent / len(pairs):.0%} are concurrent (neither could have influenced the other)')
print('  Lamport timestamps put those pairs in an order anyway. The order is consistent, but for concurrent events it is arbitrary.')

print('\nPART D  how far does each kind of timestamp stray from real time?')
drift = max(abs(e['hlc'][0] - e['true']) for e in events)
print(f'  hybrid clock: at most {drift:.0f} ms from true time (bounded by the clock skew)')
print(f'  Lamport counter: reached {max(lamport):,} after {now / 1000:.0f} seconds; it has no relation to time at all')
