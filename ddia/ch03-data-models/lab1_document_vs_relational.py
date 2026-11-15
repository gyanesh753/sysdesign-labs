# lab1_document_vs_relational.py - DDIA Ch 3: the same profiles as normalized tables and as JSON documents
import json
import random
import sqlite3
import time

random.seed(3)
N = 20_000
ORGS = [f'Org {i}' for i in range(200)]
TITLES = ['Engineer', 'Manager', 'Analyst', 'Designer']

con = sqlite3.connect(':memory:')
con.executescript('''
CREATE TABLE orgs(id INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE positions(user_id INT, org_id INT, title TEXT);
CREATE INDEX pos_user ON positions(user_id);
CREATE INDEX pos_org ON positions(org_id);
CREATE TABLE docs(id INTEGER PRIMARY KEY, body TEXT);
''')
con.executemany('INSERT INTO orgs VALUES (?,?)', enumerate(ORGS))
for u in range(N):
    jobs = [(random.randrange(len(ORGS)), random.choice(TITLES)) for _ in range(random.randint(1, 4))]
    con.execute('INSERT INTO users VALUES (?,?)', (u, f'user{u}'))
    con.executemany('INSERT INTO positions VALUES (?,?,?)', [(u, o, t) for o, t in jobs])
    # Document model: one self-contained profile. The organization NAME is copied into every profile.
    doc = {'name': f'user{u}', 'positions': [{'org': ORGS[o], 'title': t} for o, t in jobs]}
    con.execute('INSERT INTO docs VALUES (?,?)', (u, json.dumps(doc)))
con.commit()


def timed(fn):
    t = time.perf_counter()
    result = fn()
    return result, (time.perf_counter() - t) * 1000


ids = [random.randrange(N) for _ in range(5_000)]


def profile_relational(u):
    name = con.execute('SELECT name FROM users WHERE id=?', (u,)).fetchone()[0]
    jobs = con.execute('SELECT o.name, p.title FROM positions p JOIN orgs o ON o.id=p.org_id WHERE p.user_id=?', (u,)).fetchall()
    return name, jobs


def profile_document(u):
    return json.loads(con.execute('SELECT body FROM docs WHERE id=?', (u,)).fetchone()[0])


print('TASK 1  load 5,000 whole profiles (one-to-many, the tree-shaped case)')
_, ms = timed(lambda: [profile_relational(u) for u in ids])
print(f'  relational: 2 queries and a join per profile   {ms:7.1f} ms')
_, ms = timed(lambda: [profile_document(u) for u in ids])
print(f'  document:   1 read per profile                 {ms:7.1f} ms')

print('\nTASK 2  rename "Org 7" (many-to-one: many profiles point at one organization)')
_, ms = timed(lambda: con.execute("UPDATE orgs SET name='Org Seven' WHERE id=7").rowcount)
print(f'  relational: rows changed = 1                   {ms:7.1f} ms')


def rename_in_documents():
    changed = 0
    for i, body in con.execute('SELECT id, body FROM docs').fetchall():
        doc = json.loads(body)
        hit = [p for p in doc['positions'] if p['org'] == 'Org 7']
        if hit:
            for p in hit:
                p['org'] = 'Org Seven'
            con.execute('UPDATE docs SET body=? WHERE id=?', (json.dumps(doc), i))
            changed += 1
    return changed


changed, ms = timed(rename_in_documents)
print(f'  document:   documents rewritten = {changed:<6}       {ms:7.1f} ms   (and every one must succeed, or the data disagrees)')

print('\nTASK 3  who has ever worked at org 42? (many-to-many, asked from the other side)')
rows, ms = timed(lambda: con.execute('SELECT DISTINCT user_id FROM positions WHERE org_id=42').fetchall())
print(f'  relational: index lookup, {len(rows)} people           {ms:7.1f} ms')
rows2, ms = timed(lambda: con.execute("SELECT DISTINCT d.id FROM docs d, json_each(d.body, '$.positions') p WHERE json_extract(p.value, '$.org')='Org 42'").fetchall())
print(f'  document:   scan every document, {len(rows2)} people    {ms:7.1f} ms')
assert {r[0] for r in rows} == {r[0] for r in rows2}
