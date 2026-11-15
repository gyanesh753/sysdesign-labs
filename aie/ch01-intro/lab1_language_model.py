# lab1_language_model.py - AIE Ch 1: a language model from nothing but counting, trained without a single label
import random
from collections import Counter, defaultdict

random.seed(1)

# A made-up corpus. Real models read a large part of the internet; the principle is the same.
WHO = ['the engineer', 'the analyst', 'the model', 'the team', 'a user', 'the reviewer']
DOES = {'the engineer': ['deploys', 'tests', 'trains'], 'the analyst': ['queries', 'reads', 'tests'], 'the model': ['predicts', 'generates', 'completes'],
        'the team': ['reviews', 'ships', 'tests'], 'a user': ['asks', 'reads', 'rates'], 'the reviewer': ['reads', 'rates', 'reviews']}
WHAT = {'deploys': ['the model', 'the service'], 'tests': ['the model', 'the prompt', 'the service'], 'trains': ['the model'], 'queries': ['the database', 'the logs'],
        'reads': ['the report', 'the logs', 'the answer'], 'predicts': ['the next token', 'the answer'], 'generates': ['the answer', 'the report'],
        'completes': ['the sentence', 'the prompt'], 'reviews': ['the report', 'the prompt'], 'ships': ['the service', 'the model'], 'asks': ['a question'], 'rates': ['the answer']}
WHEN = ['every morning', 'after lunch', 'before the release', 'on friday', '']


def sentence():
    who = random.choice(WHO)
    verb = random.choice(DOES[who])
    return f'{who} {verb} {random.choice(WHAT[verb])} {random.choice(WHEN)}'.split() + ['.']


corpus = [sentence() for _ in range(3_000)]
vocab = sorted({t for s in corpus for t in s})
print(f'corpus: {len(corpus):,} sentences, {sum(map(len, corpus)):,} tokens, vocabulary of {len(vocab)} tokens\n')

print('PART A  self-supervision: the text labels itself')
example = corpus[0]
print(f'  one sentence: {" ".join(example)}')
for i in range(1, min(len(example), 6)):
    print(f'    context: {" ".join(example[:i]):<34} -> next token to predict: {example[i]}')
print('  Nobody annotated anything. Every position in every sentence is a free training example.')

# Train: count which token follows each pair of tokens.
follows = defaultdict(Counter)
for s in corpus:
    padded = ['<s>', '<s>'] + s
    for a, b, c in zip(padded, padded[1:], padded[2:]):
        follows[(a, b)][c] += 1


def next_distribution(a, b):
    counts = follows[(a, b)]
    total = sum(counts.values())
    return {t: n / total for t, n in counts.most_common()}


print('\nPART B  the model is a table of probabilities for the next token')
for context in [('the', 'engineer'), ('the', 'model'), ('predicts', 'the')]:
    dist = next_distribution(*context)
    print(f'  after "{" ".join(context)}": ' + ', '.join(f'{t} {p:.0%}' for t, p in list(dist.items())[:4]))


def complete(prompt, greedy):
    tokens = ['<s>', '<s>'] + prompt.split()
    while tokens[-1] != '.' and len(tokens) < 20:
        dist = next_distribution(tokens[-2], tokens[-1])
        if not dist:
            break
        tokens.append(max(dist, key=dist.get) if greedy else random.choices(list(dist), list(dist.values()))[0])
    return ' '.join(tokens[2:])


print('\nPART C  autoregressive generation: predict a token, append it, repeat')
print(f'  always the most likely token: {complete("the engineer", greedy=True)}')
for _ in range(3):
    print(f'  sampled:                      {complete("the engineer", greedy=False)}')

print('\nPART D  filling a blank needs context from BOTH sides (the masked style)')
left, right = ('<s>', 'the'), 'predicts'
scores = {w: p * follows[('the', w)][right] / max(1, sum(follows[('the', w)].values())) for w, p in next_distribution(*left).items()}
best = max(scores, key=scores.get)
print(f'  "the ___ predicts the answer"  ->  left context alone suggests "{max(next_distribution(*left), key=next_distribution(*left).get)}", using both sides gives "{best}"')

print(f'\nThis model remembers 2 tokens of context in a table with {len(follows)} rows. Remembering 1,000 tokens this way would need')
print(f'more rows than there are atoms in the universe ({len(vocab)}^1000), which is why real models compute the distribution with a neural network.')
