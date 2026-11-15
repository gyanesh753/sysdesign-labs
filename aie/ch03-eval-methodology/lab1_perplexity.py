# lab1_perplexity.py - AIE Ch 3: entropy, cross entropy and perplexity, computed on a model small enough to inspect
import math
import random
from collections import Counter, defaultdict

random.seed(3)

print('PART A  entropy: how many bits, on average, does it take to say what happened?')
for name, probs in [('fair coin', [0.5, 0.5]), ('loaded coin (90/10)', [0.9, 0.1]), ('fair six-sided die', [1 / 6] * 6), ('32 equally likely tokens', [1 / 32] * 32)]:
    h = -sum(p * math.log2(p) for p in probs)
    print(f'  {name:<26} entropy {h:4.2f} bits   perplexity {2 ** h:5.2f}   (like choosing among {2 ** h:.1f} equally likely options)')

# A small made-up language, as in chapter 1.
WHO = ['the engineer', 'the analyst', 'the model', 'the team', 'a user']
DOES = ['tests', 'reviews', 'ships', 'reads', 'rates']
WHAT = ['the model', 'the prompt', 'the report', 'the answer', 'the service']
WHEN = ['every morning', 'after lunch', 'on friday', '']
sentence = lambda: f'{random.choice(WHO)} {random.choice(DOES)} {random.choice(WHAT)} {random.choice(WHEN)}'.split() + ['.']
train = [sentence() for _ in range(4_000)]
SECRET = 'the launch code is seven four nine one .'.split()          # one unusual sentence the model sees many times
train += [SECRET] * 30
vocab = sorted({t for s in train for t in s} | {'<unk>'})
follows = defaultdict(Counter)
for s in train:
    for a, b in zip(['<s>'] + s, s):
        follows[a][b] += 1


def prob(prev, token, k=0.01):                                           # bigram model with a little smoothing
    counts = follows[prev]
    return (counts[token] + k) / (sum(counts.values()) + k * len(vocab))


def perplexity(sentences):
    bits, n = 0.0, 0
    for s in sentences:
        for a, b in zip(['<s>'] + s, s):
            bits += -math.log2(prob(a, b if b in vocab else '<unk>'))
            n += 1
    return bits / n, 2 ** (bits / n)


held_out = [sentence() for _ in range(1_000)]
shuffled = [random.sample(s, len(s)) for s in held_out]
gibberish = [[random.choice(vocab) for _ in range(7)] for _ in range(1_000)]
print('\nPART B  cross entropy and perplexity of the model on three kinds of text')
print(f'  {"text":<44}{"bits per token":>15}{"perplexity":>12}')
for name, text in [('new sentences in the language it learned', held_out), ('the same sentences with words shuffled', shuffled), ('random tokens from the vocabulary', gibberish)]:
    bits, ppl = perplexity(text)
    print(f'  {name:<44}{bits:>15.2f}{ppl:>12.1f}')
print(f'  The vocabulary has {len(vocab)} tokens, so a model that knew nothing would score a perplexity of {len(vocab)}.')
print('  The model scores far worse than that on scrambled text: being confidently wrong costs much more than being unsure.')

print('\nPART C  low perplexity can mean "I have seen exactly this before"')
novel = 'the launch date is seven four nine one .'.split()
for name, s in [('sentence repeated 30 times in training', SECRET), ('same sentence with one word changed', novel)]:
    bits, ppl = perplexity([s])
    print(f'  {name:<44}{bits:>15.2f}{ppl:>12.1f}')
print('  This is one way to test whether a benchmark, or a private document, was in a model\'s training data.')
