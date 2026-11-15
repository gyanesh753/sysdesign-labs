# lab3_cdc.py - DDIA Ch 12: keeping a cache and a search index in step with a database: dual writes versus change data capture
import random
import sqlite3

random.seed(12)

print('PART A  dual writes: two clients each update the database, then the cache')
TRIALS = 100_000
diverged = 0
for _ in range(TRIALS):
    # Each client's two steps happen in order, but the two clients interleave at random.
    steps = [('c1', 'db'), ('c1', 'cache'), ('c2', 'db'), ('c2', 'cache')]
    while True:
        random.shuffle(steps)
        if steps.index(('c1', 'db')) < steps.index(('c1', 'cache')) and steps.index(('c2', 'db')) < steps.index(('c2', 'cache')):
            break
    state = {}
    for client, system in steps:
        state[system] = client                             # last writer wins in each system separately
    diverged += state['db'] != state['cache']
print(f'  database and cache end up holding DIFFERENT values in {diverged / TRIALS:.1%} of races, and nothing ever corrects it')

print('\nPART B  change data capture: the database is the only thing written to; everything else follows its change log')
db = sqlite3.connect(':memory:')
db.executescript('''
CREATE TABLE products(id INTEGER PRIMARY KEY, name TEXT, price INT);
CREATE TABLE changes(seq INTEGER PRIMARY KEY AUTOINCREMENT, op TEXT, id INT, name TEXT, price INT);
CREATE TRIGGER cdc_i AFTER INSERT ON products BEGIN INSERT INTO changes(op,id,name,price) VALUES ('upsert', NEW.id, NEW.name, NEW.price); END;
CREATE TRIGGER cdc_u AFTER UPDATE ON products BEGIN INSERT INTO changes(op,id,name,price) VALUES ('upsert', NEW.id, NEW.name, NEW.price); END;
CREATE TRIGGER cdc_d AFTER DELETE ON products BEGIN INSERT INTO changes(op,id) VALUES ('delete', OLD.id); END;
''')
WORDS = ['red', 'blue', 'steel', 'wooden', 'chair', 'table', 'lamp', 'shelf']


class Follower:
    """Derived data: a cache (id -> row) and a search index (word -> ids). It remembers how far it has read."""

    def __init__(self):
        self.position, self.cache, self.index = 0, {}, {}

    def catch_up(self, limit=None):
        rows = db.execute('SELECT seq, op, id, name, price FROM changes WHERE seq > ? ORDER BY seq' + (f' LIMIT {limit}' if limit else ''), (self.position,)).fetchall()
        for seq, op, id_, name, price in rows:              # strictly in the order the database committed them
            for word in (self.cache.get(id_) or ('', 0))[0].split():
                self.index[word].discard(id_)
            if op == 'delete':
                self.cache.pop(id_, None)
            else:
                self.cache[id_] = (name, price)
                for word in name.split():
                    self.index.setdefault(word, set()).add(id_)
            self.position = seq
        return len(rows)


def random_write():
    r, id_ = random.random(), random.randrange(200)
    name = ' '.join(random.sample(WORDS, 2))
    if r < 0.5:
        db.execute('INSERT INTO products VALUES (?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name, price=excluded.price', (id_, name, random.randrange(500)))
    elif r < 0.85:
        db.execute('UPDATE products SET price=? WHERE id=?', (random.randrange(500), id_))
    else:
        db.execute('DELETE FROM products WHERE id=?', (id_,))


follower = Follower()
for _ in range(3_000):
    random_write()
applied = follower.catch_up(limit=1_000)                    # the follower is slow: it has only read part of the log
behind = db.execute('SELECT COUNT(*) FROM changes').fetchone()[0] - follower.position
print(f'  after 3,000 writes the follower has applied {applied:,} changes and is {behind:,} behind: stale, but not wrong')
saved_position = follower.position                          # ...then it crashes and restarts from its saved position
for _ in range(2_000):
    random_write()
follower.catch_up()
truth = {i: (n, p) for i, n, p in db.execute('SELECT id, name, price FROM products')}
index_truth = {}
for i, (name, _) in truth.items():
    for word in name.split():
        index_truth.setdefault(word, set()).add(i)
assert follower.cache == truth and {w: s for w, s in follower.index.items() if s} == index_truth
print(f'  it resumed from change {saved_position:,}, caught up, and now cache and search index match the database exactly ({len(truth)} products)')
print(f'  search for "wooden chair": {len(follower.index["wooden"] & follower.index["chair"])} products, answered without touching the database')
