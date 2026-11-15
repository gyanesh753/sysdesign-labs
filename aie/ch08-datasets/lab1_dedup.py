# lab1_dedup.py - AIE Ch 8: finding duplicates and near-duplicates in a training set without comparing every pair
import hashlib
import random
import re
import time

random.seed(8)
TOPICS = ['invoices', 'passwords', 'refunds', 'delivery times', 'student discounts', 'data exports', 'team workspaces', 'login alerts', 'tax receipts', 'trial periods']
VERBS = ['explain', 'summarize', 'list the steps for', 'describe the policy on', 'write a short note about', 'give two examples of']
AUDIENCES = ['a new customer', 'a support agent', 'a finance manager', 'a developer', 'a school administrator', 'a small business owner']
DETAILS = ['in plain language', 'in three sentences', 'with one example', 'as a numbered list', 'without jargon', 'for a mobile screen', 'in a friendly tone', 'for an internal wiki']

base = list({f'{v.capitalize()} {t} for {a}, {d}.' for v in VERBS for t in TOPICS for a in AUDIENCES for d in DETAILS})
random.shuffle(base)
base = base[:2_000]
exact = random.sample(base, 150)                                               # copied as is
cosmetic = [(s, f'  {s.upper()}  ' if i % 2 else s.replace(' ', '  ').rstrip('.')) for i, s in enumerate(random.sample(base, 150))]   # same text, different casing/spacing
near = [(s, s.replace(' for ', ' aimed at ', 1)) for s in random.sample(base, 150)]  # one word changed
tagged = [(s, s) for s in base] + [(s, s) for s in exact] + cosmetic + near    # (the original it came from, the text)
random.shuffle(tagged)
source = [o for o, _ in tagged]
data = [t for _, t in tagged]
print(f'{len(data):,} examples: {len(base):,} originals + 150 exact copies + 150 cosmetic copies + 150 reworded copies\n')

normalize = lambda s: re.sub(r'[^a-z0-9 ]', '', re.sub(r'\s+', ' ', s.lower())).strip()
shingles = lambda s: {' '.join(w) for w in zip(*(normalize(s).split()[i:] for i in range(2)))}     # overlapping word pairs


def jaccard(a, b):
    return len(a & b) / len(a | b)


def by_hash(key):
    seen, removed = set(), 0
    for s in data:
        h = hashlib.md5(key(s).encode()).hexdigest()
        removed += h in seen
        seen.add(h)
    return removed


t = time.perf_counter()
exact_removed = by_hash(lambda s: s)
t_exact = time.perf_counter() - t
t = time.perf_counter()
norm_removed = by_hash(normalize)
t_norm = time.perf_counter() - t

# Near-duplicates. MinHash: summarize each example by a short signature so that similar examples get similar signatures.
SIGNATURE, BANDS = 60, 20
salts = [str(random.random()) for _ in range(SIGNATURE)]
t = time.perf_counter()
sets = [shingles(s) for s in data]
signatures = [[min(hash(salt + sh) for sh in st) for salt in salts] for st in sets]
buckets, candidates = {}, set()
rows = SIGNATURE // BANDS
for i, sig in enumerate(signatures):
    for b in range(BANDS):                                                     # examples that agree on any whole band become candidates
        key = (b, tuple(sig[b * rows:(b + 1) * rows]))
        for j in buckets.get(key, []):
            candidates.add((j, i))
        buckets.setdefault(key, []).append(i)
t_near = time.perf_counter() - t
confirmed = {(i, j): jaccard(sets[i], sets[j]) for i, j in candidates}        # check each candidate pair properly


def near_duplicates(threshold):
    """An example is removed if it closely matches an earlier one. Was that earlier one really its original?"""
    right, wrong = set(), set()
    for (i, j), similarity in confirmed.items():
        if similarity >= threshold:
            (right if source[i] == source[j] else wrong).add(max(i, j))
    return len(right), len(wrong - right)


all_pairs = len(data) * (len(data) - 1) // 2
print(f'{"method":<44}{"planted copies found":>22}{"originals wrongly removed":>27}')
print(f'{"exact hash":<44}{f"{exact_removed} of 450":>22}{0:>27}')
print(f'{"hash after normalizing case and spacing":<44}{f"{norm_removed} of 450":>22}{0:>27}')
for threshold in [0.95, 0.75, 0.6]:
    right, wrong = near_duplicates(threshold)
    print(f'{f"word-pair similarity of at least {threshold}":<44}{f"{right} of 450":>22}{wrong:>27}')
print(f'\nComparing every pair directly would take {all_pairs:,} comparisons. MinHash signatures narrowed that to {len(candidates):,} in {t_near:.2f}s.')
print('A strict threshold misses the reworded copies. A loose one finds them and also deletes examples that are merely similar,')
print('which costs you the variety the dataset needs. The threshold has to be chosen by looking at what it removes.')
