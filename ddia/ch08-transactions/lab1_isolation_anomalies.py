# lab1_isolation_anomalies.py - DDIA Ch 8: a small multi-version store, three isolation levels, three race conditions
class Abort(Exception):
    pass


class DB:
    """Every committed write is kept as (commit_number, value). Nothing is overwritten."""

    def __init__(self, level, data):
        self.level, self.clock = level, 0
        self.versions = {k: [(0, v)] for k, v in data.items()}

    def begin(self):
        return Txn(self)

    def latest_commit(self, key):
        return self.versions[key][-1][0]


class Txn:
    def __init__(self, db):
        self.db, self.snapshot, self.reads, self.writes = db, db.clock, set(), {}

    def read(self, key):
        self.reads.add(key)
        if key in self.writes:
            return self.writes[key]
        # read committed: each read sees the newest committed value.  snapshot/serializable: the world as of BEGIN.
        as_of = self.db.clock if self.db.level == 'read committed' else self.snapshot
        return [v for c, v in self.db.versions[key] if c <= as_of][-1]

    def write(self, key, value):
        self.writes[key] = value

    def commit(self):
        db = self.db
        if db.level != 'read committed':
            for key in self.writes:                       # someone else committed a change to a row I am overwriting
                if db.latest_commit(key) > self.snapshot:
                    raise Abort(f'{key} was changed by another transaction')
        if db.level == 'serializable' and self.writes:
            for key in self.reads:                        # I based a write on something that is no longer true
                if db.latest_commit(key) > self.snapshot:
                    raise Abort(f'the value of {key} I read is out of date')
        db.clock += 1
        for key, value in self.writes.items():
            db.versions[key].append((db.clock, value))


def read_skew(level):
    """An auditor adds up two accounts while a transfer moves 100 between them."""
    db = DB(level, {'A': 500, 'B': 500})
    audit, transfer = db.begin(), db.begin()
    a = audit.read('A')
    transfer.write('A', transfer.read('A') - 100)
    transfer.write('B', transfer.read('B') + 100)
    transfer.commit()
    total = a + audit.read('B')
    return f'auditor sees total {total}' + ('' if total == 1000 else '  <- money that does not exist')


def lost_update(level):
    """Two clients each read a counter, add one, and write it back."""
    db = DB(level, {'counter': 10})
    t1, t2 = db.begin(), db.begin()
    v1, v2 = t1.read('counter'), t2.read('counter')
    t1.write('counter', v1 + 1)
    t1.commit()
    t2.write('counter', v2 + 1)
    try:
        t2.commit()
        note = ''
    except Abort:
        retry = db.begin()                               # the database refused; the application tries again
        retry.write('counter', retry.read('counter') + 1)
        retry.commit()
        note = ' (second transaction aborted and retried)'
    final = db.begin().read('counter')
    return f'10 + 1 + 1 = {final}{note}' + ('' if final == 12 else '  <- one increment lost')


def write_skew(level):
    """Two linked accounts with 60 each. The bank's rule: the COMBINED balance must never go below zero.
    Each owner withdraws 100 from their own account at the same moment, after checking the combined balance."""
    db = DB(level, {'savings': 60, 'current': 60})

    def withdraw(txn, account, amount):
        if txn.read('savings') + txn.read('current') >= amount:     # the check looks at BOTH rows...
            txn.write(account, txn.read(account) - amount)          # ...but the write touches only ONE

    t1, t2 = db.begin(), db.begin()
    withdraw(t1, 'savings', 100)
    withdraw(t2, 'current', 100)
    t1.commit()
    try:
        t2.commit()
        note = ''
    except Abort:
        retry = db.begin()
        withdraw(retry, 'current', 100)                  # this time the check sees the first withdrawal and refuses
        retry.commit()
        note = ' (second transaction aborted; on retry the check refuses, correctly)'
    final = db.begin()
    combined = final.read('savings') + final.read('current')
    return f'combined balance: {combined}{note}' + ('' if combined >= 0 else '  <- rule broken, and no row was written twice')


for name, scenario in [('READ SKEW', read_skew), ('LOST UPDATE', lost_update), ('WRITE SKEW', write_skew)]:
    print(name)
    for level in ['read committed', 'snapshot isolation', 'serializable']:
        print(f'  {level:<20}{scenario(level)}')
    print()
