# lab2_similarity.py - AIE Ch 3: comparing an answer with a reference: exact match, word overlap, and meaning
from collections import Counter

import numpy as np
import requests

REFERENCE = 'The meeting was moved to Thursday afternoon.'
CANDIDATES = [
    ('identical', 'The meeting was moved to Thursday afternoon.'),
    ('same meaning, other words', 'They rescheduled the meeting for after lunch on Thursday.'),
    ('one fact wrong', 'The meeting was moved to Tuesday afternoon.'),
    ('negated', 'The meeting was not moved to Thursday afternoon.'),
    ('unrelated', 'The printer on the third floor is out of toner.'),
]

words = lambda s: s.lower().replace('.', '').split()


def token_f1(a, b):
    ca, cb = Counter(words(a)), Counter(words(b))
    overlap = sum((ca & cb).values())
    if not overlap:
        return 0.0
    precision, recall = overlap / sum(cb.values()), overlap / sum(ca.values())
    return 2 * precision * recall / (precision + recall)


def bigram_overlap(a, b):
    pairs = lambda s: Counter(zip(words(s), words(s)[1:]))
    pa, pb = pairs(a), pairs(b)
    return sum((pa & pb).values()) / max(1, sum(pb.values()))


def embed(texts):
    r = requests.post('http://localhost:11434/api/embed', json={'model': 'nomic-embed-text', 'input': texts}, timeout=120)
    v = np.array(r.json()['embeddings'])
    return v / np.linalg.norm(v, axis=1, keepdims=True)


vectors = embed([REFERENCE] + [c for _, c in CANDIDATES])
print(f'reference: {REFERENCE}\n')
print(f'{"candidate":<28}{"exact":>6}{"word F1":>9}{"bigram overlap":>16}{"embedding cosine":>18}   should count as correct?')
for (label, text), vec in zip(CANDIDATES, vectors[1:]):
    correct = 'yes' if label in ('identical', 'same meaning, other words') else 'NO'
    print(f'{label:<28}{str(text == REFERENCE):>6}{token_f1(REFERENCE, text):>9.2f}{bigram_overlap(REFERENCE, text):>16.2f}{float(vec @ vectors[0]):>18.2f}   {correct}')

print('\nRead the table by row:')
print('  - Exact match only accepts the identical answer and rejects a perfectly good paraphrase.')
print('  - Word overlap scores the wrong-fact and negated answers HIGHER than the correct paraphrase.')
print('  - Embedding similarity recognizes the paraphrase, but look at how it scores the wrong-fact and negated answers.')
print('No single number separates right from wrong here. That gap is why people turn to a model as the judge.')
