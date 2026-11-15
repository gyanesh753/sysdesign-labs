# lab3_leader_election.py - DDIA Ch 10: electing a leader by majority vote, with the network splitting at random
import random

random.seed(10)
N, ROUNDS = 5, 20_000
MAJORITY = N // 2 + 1

term = [0] * N                    # the highest term (election number) each node has heard of
last_vote = [0] * N               # a node votes at most once per term
leading = [None] * N              # the term in which this node believes it is leader, or None
leaders_of_term = {}
stats = dict(elections_won=0, elections_failed=0, rounds_with_two_believers=0, rounds_with_two_committers=0, stale_writes_rejected=0)

for _ in range(ROUNDS):
    nodes = list(range(N))
    random.shuffle(nodes)
    cut = random.choice([0, 0, 1, 2, 3, 4])           # 0 = no partition this round; otherwise split into two groups
    groups = [nodes] if cut == 0 else [nodes[:cut], nodes[cut:]]
    committers = 0
    for group in groups:
        # nodes that can talk to each other learn the highest term among them
        highest = max(term[i] for i in group)
        for i in group:
            term[i] = highest
            if leading[i] is not None and leading[i] < highest:
                leading[i] = None                     # a leader that hears of a newer term steps down
        if not any(leading[i] == highest for i in group) and random.random() < 0.5:
            candidate, new_term = random.choice(group), highest + 1
            votes = 0
            for i in group:
                if last_vote[i] < new_term:           # one vote per term
                    last_vote[i], term[i] = new_term, new_term
                    votes += 1
            if votes >= MAJORITY:
                leading[candidate] = new_term
                leaders_of_term.setdefault(new_term, set()).add(candidate)
                stats['elections_won'] += 1
            else:
                stats['elections_failed'] += 1
        # every node that believes it is leader tries to commit a write, which needs a majority to accept its term
        for b in [i for i in group if leading[i] is not None]:
            accepts = sum(1 for i in group if term[i] <= leading[b])
            if accepts >= MAJORITY:
                committers += 1
            else:
                stats['stale_writes_rejected'] += 1
    if sum(1 for i in range(N) if leading[i] is not None) > 1:
        stats['rounds_with_two_believers'] += 1
    if committers > 1:
        stats['rounds_with_two_committers'] += 1

print(f'{N} nodes, {ROUNDS:,} rounds, the network splits into two groups in two rounds out of three\n')
print(f'elections won by a majority:                      {stats["elections_won"]:>7,}')
print(f'elections that failed (candidate in a minority):  {stats["elections_failed"]:>7,}')
print(f'terms with more than one leader:                  {sum(1 for s in leaders_of_term.values() if len(s) > 1):>7,}   <- must be 0')
print(f'rounds where two nodes BELIEVED they were leader: {stats["rounds_with_two_believers"]:>7,}   <- allowed, and it happens')
print(f'rounds where two leaders could commit a write:    {stats["rounds_with_two_committers"]:>7,}   <- must be 0')
print(f'writes from an out-of-date leader rejected:       {stats["stale_writes_rejected"]:>7,}')
assert all(len(s) == 1 for s in leaders_of_term.values()) and stats['rounds_with_two_committers'] == 0
