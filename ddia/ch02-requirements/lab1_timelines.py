# lab1_timelines.py - DDIA Ch 2: home timelines, three designs
import time
import numpy as np
from collections import defaultdict

rng = np.random.default_rng(7)
USERS = 10_000
CELEB = 1_000                     # accounts with more followers than this are 'celebrities'

# Popularity-skewed follow graph: everyone follows 20-300 accounts, popular accounts are followed far more often
weights = 1 / np.arange(1, USERS + 1) ** 0.9
weights /= weights.sum()
following, followers = {}, defaultdict(list)
for u in range(USERS):
    k = int(rng.integers(20, 300))
    targets = rng.choice(USERS, size=k, replace=False, p=weights)
    following[u] = targets.tolist()
    for t in targets:
        followers[int(t)].append(u)
celeb = {u for u in range(USERS) if len(followers[u]) > CELEB}
celeb_follows = {u: [t for t in following[u] if t in celeb] for u in range(USERS)}
print(f'users={USERS}, celebrities={len(celeb)}, max followers={max(len(v) for v in followers.values())}, '
      f'avg following={np.mean([len(v) for v in following.values()]):.0f}')

# ---- A: fan-out on READ (query-time merge) ----
posts_by_user = defaultdict(list)
def post_a(a, pid): posts_by_user[a].append(pid)
def read_a(v):
    items = []
    for u in following[v]:
        items.extend(posts_by_user[u][-20:])
    items.sort(reverse=True)
    return items[:50]

# ---- B: fan-out on WRITE (materialized timelines) ----
timelines = defaultdict(list)
def post_b(a, pid):
    for f in followers[a]:
        timelines[f].append(pid)
def read_b(v): return timelines[v][-50:][::-1]

# ---- C: hybrid (celebrity posts stored once, merged at read time) ----
timelines_c, celeb_posts = defaultdict(list), defaultdict(list)
def post_c(a, pid):
    if a in celeb:
        celeb_posts[a].append(pid)
    else:
        for f in followers[a]:
            timelines_c[f].append(pid)
def read_c(v):
    items = timelines_c[v][-50:]
    for u in celeb_follows[v]:
        items = items + celeb_posts[u][-20:]
    return sorted(items, reverse=True)[:50]

def timed(label, fn, args_list):
    ts = []
    for args in args_list:
        t = time.perf_counter(); fn(*args); ts.append((time.perf_counter() - t) * 1e6)
    p = np.percentile(ts, [50, 99, 100])
    print(f'{label:<20} p50={p[0]:9.1f}us  p99={p[1]:10.1f}us  max={p[2]:11.1f}us')

N_POSTS = 60_000
authors = rng.integers(0, USERS, N_POSTS)
writes = [(int(a), pid) for pid, a in enumerate(authors)]
fan = np.array([len(followers[a]) for a, _ in writes])
print(f'\nfan-out per post: mean={fan.mean():.0f}, p99={np.percentile(fan, 99):.0f}, max={fan.max()}')

print('\n--- write path (per post) ---')
timed('A (just append)', post_a, writes)
timed('B (fan-out)', post_b, writes)
timed('C (hybrid)', post_c, writes)

viewers = [(int(v),) for v in rng.integers(0, USERS, 3000)]
print('\n--- read path (load a timeline) ---')
timed('A (merge at read)', read_a, viewers)
timed('B (precomputed)', read_b, viewers)
timed('C (hybrid)', read_c, viewers)
