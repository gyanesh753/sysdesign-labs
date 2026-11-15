# lab1_log_broker.py - DDIA Ch 12: a log-based message broker in memory: partitions, offsets, redelivery, replay, compaction
import random
import zlib

random.seed(12)
PARTITIONS = 3


class Log:
    """An append-only log per partition. Reading does not remove anything; a consumer only remembers an offset."""

    def __init__(self):
        self.partitions = [[] for _ in range(PARTITIONS)]

    def append(self, key, value):
        p = zlib.crc32(key.encode()) % PARTITIONS          # same key -> same partition -> order preserved per key
        self.partitions[p].append((key, value))
        return p, len(self.partitions[p]) - 1


log = Log()
USERS = [f'user{i}' for i in range(50)]
payments = [(random.choice(USERS), random.randint(1, 100)) for _ in range(3_000)]
for user, amount in payments:
    log.append(user, amount)
TRUE_TOTAL = sum(a for _, a in payments)
print(f'{len(payments):,} payment events in {PARTITIONS} partitions {[len(p) for p in log.partitions]}, true total {TRUE_TOTAL:,}\n')


def consume(idempotent, crash_every=400, commit_every=50):
    """Sum all payments. The consumer commits its offset every 50 records and crashes now and then before committing."""
    total, committed, redelivered = 0, [0] * PARTITIONS, 0
    applied_up_to = [0] * PARTITIONS                       # idempotent version: stored together with the total
    handled = 0
    for p in range(PARTITIONS):
        offset = committed[p]
        while offset < len(log.partitions[p]):
            _, amount = log.partitions[p][offset]
            if not idempotent or offset >= applied_up_to[p]:
                total += amount
                applied_up_to[p] = offset + 1
            offset += 1
            handled += 1
            if offset % commit_every == 0:
                committed[p] = offset
            if handled % crash_every == 0:                 # crash: everything after the last commit is delivered again
                redelivered += offset - committed[p]
                offset = committed[p]
        committed[p] = offset
    return total, redelivered


print('PART A  a consumer that crashes before committing its offset gets the same messages again')
for idempotent in (False, True):
    total, redelivered = consume(idempotent)
    label = 'remembers which offsets it has applied' if idempotent else 'just adds every message it receives'
    print(f'  {label:<42} total = {total:>8,}  ({redelivered} messages redelivered, error {total - TRUE_TOTAL:+,})')

print('\nPART B  ordering: guaranteed within a partition, not across partitions')
p0 = [k for k, _ in log.partitions[0]]
print(f'  partition 0 holds only {len(set(p0))} of the {len(USERS)} users; each user\'s events are all in one partition, in the order sent')

print('\nPART C  replay: a new consumer starts at offset 0 and builds a different view from the same log')
per_user = {}
for part in log.partitions:
    for user, amount in part:
        per_user[user] = per_user.get(user, 0) + amount
top = max(per_user, key=per_user.get)
print(f'  per-user totals built months later from the old events; biggest spender {top} with {per_user[top]:,}')
print('  A queue that deletes each message once it is acknowledged would have nothing left to replay.')

print('\nPART D  log compaction: keep only the newest record for each key')
changes = Log()
for _ in range(20_000):
    user = random.choice(USERS)
    changes.append(user, {'email': f'{user}+{random.randrange(10**6)}@example.com'})   # a changelog of profile updates
before = sum(len(p) for p in changes.partitions)
latest = {}
for part in changes.partitions:
    for key, value in part:
        latest[key] = value                                # later records for a key replace earlier ones
print(f'  {before:,} records -> {len(latest)} after compaction, and replaying either one rebuilds the same {len(latest)} current profiles')
