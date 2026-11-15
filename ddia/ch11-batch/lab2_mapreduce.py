# lab2_mapreduce.py - DDIA Ch 11: a minimal MapReduce: map, shuffle, reduce, a join, a two-step workflow, and a failed task
import itertools
import random
from collections import defaultdict

import duckdb
import pandas as pd

random.seed(11)


class TaskFailed(Exception):
    pass


def run_job(name, splits, mapper, reducer, reducers=4, fail_once=None):
    """splits: list of lists of records. Returns one output list per reducer. Inputs are never modified."""
    attempts = 0
    partitions = [[] for _ in range(reducers)]
    for i, split in enumerate(splits):                      # --- map phase: one task per input split ---
        while True:
            attempts += 1
            out = []                                        # a task's output only counts if the task finishes
            try:
                for n, record in enumerate(split):
                    if fail_once == i and attempts == i + 1 and n == len(split) // 2:
                        raise TaskFailed                    # the machine dies halfway through this task
                    out.extend(mapper(record))
                break
            except TaskFailed:
                print(f'  [{name}] map task {i} failed halfway; its partial output is thrown away and the task is run again')
        for key, value in out:
            partitions[hash(key) % reducers].append((key, value))
    results = []
    for part in partitions:                                 # --- shuffle: sort by key so equal keys are adjacent ---
        part.sort(key=lambda kv: (kv[0], kv[1]))
        out = []
        for key, group in itertools.groupby(part, key=lambda kv: kv[0]):   # --- reduce: one call per key ---
            out.extend(reducer(key, [v for _, v in group]))
        results.append(out)
    return results, attempts


COUNTRIES = ['IN', 'US', 'AE', 'DE', 'BR']
users = [(u, random.choice(COUNTRIES)) for u in range(2_000)]
views = [(random.randrange(2_000), f'/page/{random.randrange(50)}') for _ in range(40_000)]
splits = [[('user', u) for u in users[i::2]] for i in range(2)] + [[('view', v) for v in views[i::4]] for i in range(4)]


# Job 1: join page views to users. Both kinds of record are keyed by user ID so they meet in the same reducer.
def join_mapper(record):
    kind, (user_id, payload) = record
    yield user_id, ('0country', payload) if kind == 'user' else ('1view', payload)    # sorts the user record first


def join_reducer(user_id, values):
    country = values[0][1]                                  # thanks to the sort, the user record comes first
    for _, url in values[1:]:
        yield country, url


# Job 2: count views per country. Its input is job 1's output: a workflow of two jobs.
def count_mapper(record):
    country, _ = record
    yield country, 1


def count_reducer(country, ones):
    yield country, sum(ones)


def workflow(fail_once=None):
    joined, a1 = run_job('join', splits, join_mapper, join_reducer, fail_once=fail_once)
    counted, a2 = run_job('count', joined, count_mapper, count_reducer)
    return dict(kv for part in counted for kv in part), a1 + a2


print('Run 1: no failures')
result, attempts = workflow()
print(f'  {attempts} task attempts -> {dict(sorted(result.items()))}')

print('\nRun 2: one map task crashes halfway')
result2, attempts2 = workflow(fail_once=3)
print(f'  {attempts2} task attempts -> {dict(sorted(result2.items()))}')
assert result == result2
print('  identical output: tasks are deterministic and inputs are immutable, so a retry is always safe')

users_df = pd.DataFrame(users, columns=['user_id', 'country'])
views_df = pd.DataFrame(views, columns=['user_id', 'url'])
sql = dict(duckdb.sql('SELECT country, COUNT(*) FROM views_df JOIN users_df USING (user_id) GROUP BY country').fetchall())
assert sql == result
print('\nThe same answer from one line of SQL (checked): SELECT country, COUNT(*) FROM views JOIN users USING (user_id) GROUP BY country')
