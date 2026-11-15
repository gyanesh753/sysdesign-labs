# lab2_graph_queries.py - DDIA Ch 3: a property graph stored in two tables, queried with recursive SQL and with a graph library
import random
import sqlite3
import time

import networkx as nx

random.seed(5)
con = sqlite3.connect(':memory:')
con.executescript('''
CREATE TABLE vertices(id INTEGER PRIMARY KEY, label TEXT, name TEXT);
CREATE TABLE edges(tail INT, head INT, label TEXT);
CREATE INDEX edges_tail ON edges(tail, label);
CREATE INDEX edges_head ON edges(head, label);
''')
G = nx.MultiDiGraph()
next_id = 0


def vertex(label, name):
    global next_id
    next_id += 1
    con.execute('INSERT INTO vertices VALUES (?,?,?)', (next_id, label, name))
    G.add_node(next_id, label=label, name=name)
    return next_id


def edge(tail, head, label):
    con.execute('INSERT INTO edges VALUES (?,?,?)', (tail, head, label))
    G.add_edge(tail, head, label=label)


# Places nest to DIFFERENT depths: some countries have regions, some regions have districts. That is what makes this awkward in plain SQL.
cities = []
for continent in ['Asia', 'Europe', 'Africa', 'Americas']:
    c = vertex('continent', continent)
    for i in range(6):
        country = vertex('country', f'{continent}-country{i}')
        edge(country, c, 'within')
        parent = country
        for depth in range(random.randint(0, 3)):          # 0 to 3 extra levels
            sub = vertex('region', f'{continent}-c{i}-level{depth}')
            edge(sub, parent, 'within')
            parent = sub
        for k in range(4):
            city = vertex('city', f'{continent}-c{i}-city{k}')
            edge(city, parent, 'within')
            cities.append(city)
people = []
for p in range(3_000):
    person = vertex('person', f'person{p}')
    edge(person, random.choice(cities), 'born_in')
    edge(person, random.choice(cities), 'lives_in')
    people.append(person)
for person in people:
    for friend in random.sample(people, 3):
        edge(person, friend, 'knows')
con.commit()

print('QUERY 1  people born anywhere in Asia who now live anywhere in Europe')
SQL = '''
WITH RECURSIVE
  in_asia(id)   AS (SELECT id FROM vertices WHERE name='Asia'
                    UNION SELECT e.tail FROM edges e JOIN in_asia ON e.head=in_asia.id WHERE e.label='within'),
  in_europe(id) AS (SELECT id FROM vertices WHERE name='Europe'
                    UNION SELECT e.tail FROM edges e JOIN in_europe ON e.head=in_europe.id WHERE e.label='within')
SELECT p.id FROM vertices p
  JOIN edges b ON b.tail=p.id AND b.label='born_in'  JOIN in_asia   ON b.head=in_asia.id
  JOIN edges l ON l.tail=p.id AND l.label='lives_in' JOIN in_europe ON l.head=in_europe.id'''
t = time.perf_counter()
sql_result = {r[0] for r in con.execute(SQL)}
print(f'  recursive SQL: {len(sql_result)} people, {(time.perf_counter() - t) * 1000:.1f} ms, {len(SQL.split())} words of query')

within = nx.DiGraph((u, v) for u, v, d in G.edges(data=True) if d['label'] == 'within')
name_to_id = {d['name']: n for n, d in G.nodes(data=True)}
t = time.perf_counter()
asia = nx.ancestors(within, name_to_id['Asia'])            # everything with a 'within' path to Asia, any depth
europe = nx.ancestors(within, name_to_id['Europe'])
graph_result = set()
for person in people:
    out = {d['label']: v for _, v, d in G.out_edges(person, data=True) if d['label'] != 'knows'}
    if out['born_in'] in asia and out['lives_in'] in europe:
        graph_result.add(person)
print(f'  graph traversal: {len(graph_result)} people, {(time.perf_counter() - t) * 1000:.1f} ms')
assert sql_result == graph_result
depths = sorted({nx.shortest_path_length(within, c, name_to_id[G.nodes[c]["name"].split("-")[0]]) for c in cities})
print(f'  a city is {depths[0]} to {depths[-1]} "within" hops from its continent, so no fixed number of joins works')

print('\nQUERY 2  how many people can person0 reach through "knows" in at most k hops?')
knows = nx.DiGraph((u, v) for u, v, d in G.edges(data=True) if d['label'] == 'knows')
start = people[0]
for k in range(1, 6):
    reach_sql = con.execute('''
        WITH RECURSIVE reach(id, depth) AS (SELECT ?, 0
            UNION SELECT e.head, r.depth+1 FROM edges e JOIN reach r ON e.tail=r.id WHERE e.label='knows' AND r.depth < ?)
        SELECT COUNT(DISTINCT id) - 1 FROM reach''', (start, k)).fetchone()[0]
    reach_nx = len(nx.single_source_shortest_path_length(knows, start, cutoff=k)) - 1
    assert reach_sql == reach_nx
    print(f'  k={k}: {reach_sql:>5} people')
