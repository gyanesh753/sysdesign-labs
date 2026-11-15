# lab3_fencing.py - DDIA Ch 9: a lease, a long pause, and a client that does not know its lease has expired
import random

random.seed(9)
LEASE_MS = 10_000


class LockService:
    def __init__(self):
        self.holder, self.expires, self.token = None, 0, 100

    def acquire(self, client, now):
        if self.holder is None or now >= self.expires:
            self.holder, self.expires = client, now + LEASE_MS
            self.token += 1                              # a number that only ever goes up
            return self.token
        return None


class Storage:
    def __init__(self, check_tokens):
        self.check_tokens, self.highest, self.data, self.log = check_tokens, 0, None, []

    def write(self, client, token, value):
        if self.check_tokens and token < self.highest:
            self.log.append(f'{client} REJECTED (token {token} is older than {self.highest})')
            return False
        self.highest = max(self.highest, token)
        self.data = value
        self.log.append(f'{client} wrote {value!r} with token {token}')
        return True


def scenario(check_tokens, pause_ms, verbose=False):
    lock, store, now = LockService(), Storage(check_tokens), 0
    token1 = lock.acquire('client 1', now)               # client 1 gets the lease...
    still_valid = now < lock.expires                     # ...and even checks it is valid right before writing
    now += pause_ms                                      # then the process stops: garbage collection, VM paused, laptop lid closed
    token2 = lock.acquire('client 2', now)               # meanwhile the lease expires and client 2 takes over
    if token2:
        store.write('client 2', token2, 'new data from client 2')
    if still_valid:                                      # client 1 wakes up. From its point of view no time has passed.
        store.write('client 1', token1, 'stale data from client 1')
    if verbose:
        for line in store.log:
            print('    ' + line)
        print(f'    final content: {store.data!r}')
    return token2 is not None and store.data == 'stale data from client 1'


print('One 15-second pause while holding a 10-second lease\n')
print('  storage does NOT check tokens:')
scenario(False, 15_000, verbose=True)
print('\n  storage checks the fencing token:')
scenario(True, 15_000, verbose=True)

print('\n1,000,000 lease holders; pauses are usually tiny, occasionally very long')
pauses = [random.expovariate(1 / 50) if random.random() > 0.0002 else random.uniform(5_000, 60_000) for _ in range(1_000_000)]
for check in (False, True):
    corrupted = sum(scenario(check, p) for p in pauses)
    print(f'  fencing tokens {"on " if check else "off"}: newer data overwritten by a stale client {corrupted} times')
