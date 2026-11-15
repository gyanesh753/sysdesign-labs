# lab1_derived_views.py - DDIA Ch 13: one event log, several derived views, and what replay lets you do
import random
from collections import defaultdict

random.seed(13)
ACCOUNTS = [f'acct{i}' for i in range(20)]
MEMOS = ['rent', 'salary', 'groceries', 'refund', 'coffee', 'insurance']

# The system of record: an append-only list of things that happened. Nothing below ever modifies it.
log = []
for day in range(30):
    for _ in range(200):
        kind = random.choice(['deposit', 'withdraw', 'transfer'])
        event = {'day': day, 'kind': kind, 'account': random.choice(ACCOUNTS), 'amount': random.randint(1, 500), 'memo': random.choice(MEMOS)}
        if kind == 'transfer':
            event['to'] = random.choice([a for a in ACCOUNTS if a != event['account']])
        log.append(event)


# Each view is a pure function of the log: same events in, same view out.
def balances(events):
    view = defaultdict(int)
    for e in events:
        if e['kind'] == 'deposit':
            view[e['account']] += e['amount']
        elif e['kind'] == 'withdraw':
            view[e['account']] -= e['amount']
        else:
            view[e['account']] -= e['amount']
            view[e['to']] += e['amount']
    return dict(view)


def balances_with_bug(events):
    view = defaultdict(int)
    for e in events:
        if e['kind'] == 'deposit':
            view[e['account']] += e['amount']
        else:
            view[e['account']] -= e['amount']               # BUG: a transfer never credits the receiving account
    return dict(view)


def memo_index(events):
    view = defaultdict(list)
    for position, e in enumerate(events):
        view[e['memo']].append(position)
    return dict(view)


def daily_volume(events):
    view = defaultdict(int)
    for e in events:
        view[e['day']] += e['amount']
    return dict(view)


print(f'{len(log):,} events in the log\n')
print('1. Three different views derived from the same events')
b, idx, vol = balances(log), memo_index(log), daily_volume(log)
print(f'   balances: {len(b)} accounts | search index: {len(idx)} memo words | daily volume: {len(vol)} days')

print('\n2. A new requirement months later: largest single withdrawal per account. No migration, just another function')
largest = defaultdict(int)
for e in log:
    if e['kind'] == 'withdraw':
        largest[e['account']] = max(largest[e['account']], e['amount'])
print(f'   built for all {len(largest)} accounts from history that was recorded before anyone asked for it')

print('\n3. A bug in a view: transfers were not credited to the receiver')
wrong = balances_with_bug(log)
print(f'   money in the buggy view: {sum(wrong.values()):>9,}   accounts with a wrong balance: {sum(1 for a in b if wrong.get(a, 0) != b[a])}')
print(f'   money after fixing the code and replaying the log: {sum(b.values()):>9,}   (the events were never damaged)')

print('\n4. Changing a view safely: run old and new side by side on the same events, compare, then switch readers over')
print(f'   the new view differs from the old on {sum(1 for a in b if wrong.get(a, 0) != b[a])} of {len(b)} accounts; you inspect the differences before any user sees them')

print('\n5. Trust, but verify: a stored view can be checked by deriving it again')
stored = dict(b)
stored['acct7'] += 1                                         # one silent corruption in the stored view
fresh = balances(log)
print(f'   re-derived and compared: mismatches found in {[a for a in fresh if fresh[a] != stored[a]]}')
