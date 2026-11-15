# lab3_audit_log.py - DDIA Ch 13: making a log tamper-evident with a chain of hashes
import hashlib
import json
import random
import time

random.seed(13)


def digest(previous_hash, event):
    return hashlib.sha256((previous_hash + json.dumps(event, sort_keys=True)).encode()).hexdigest()


def append(log, event):
    previous = log[-1]['hash'] if log else '0' * 64
    log.append({'event': event, 'hash': digest(previous, event)})   # each entry commits to everything before it


def verify(log, trusted_head=None):
    previous = '0' * 64
    for position, entry in enumerate(log):
        if digest(previous, entry['event']) != entry['hash']:
            return f'entry {position:,} does not match its hash'
        previous = entry['hash']
    if trusted_head and previous != trusted_head:
        return 'the chain is self-consistent but its final hash differs from the one recorded elsewhere'
    return 'intact'


log = []
for i in range(50_000):
    append(log, {'n': i, 'account': f'acct{random.randrange(100)}', 'amount': random.randint(1, 500)})
head = log[-1]['hash']                                       # published somewhere the database operator cannot rewrite
print(f'{len(log):,} entries, final hash {head[:16]}...\n')

t = time.perf_counter()
print(f'1. untouched log:                              {verify(log, head)}  (checked in {time.perf_counter() - t:.2f}s)')

log[31_337]['event']['amount'] += 1_000                      # someone edits one old amount
print(f'2. one amount changed:                         {verify(log, head)}')
log[31_337]['event']['amount'] -= 1_000

removed = log.pop(12_345)                                    # someone deletes an entry
print(f'3. one entry deleted:                          {verify(log, head)}')
log.insert(12_345, removed)

# A careful attacker rewrites an entry AND recomputes every hash after it, so the chain is consistent again.
forged = [dict(e, event=dict(e['event'])) for e in log]
forged[40_000]['event']['amount'] = 1
previous = forged[39_999]['hash']
for entry in forged[40_000:]:
    entry['hash'] = previous = digest(previous, entry['event'])
print(f'4. entry rewritten and all later hashes redone: without an outside reference -> {verify(forged)}')
print(f'                                                with the published final hash -> {verify(forged, head)}')

truncated = log[:-10]                                        # the last ten entries quietly dropped
print(f'5. last ten entries dropped:                   {verify(truncated, head)}')
