# lab2_attention.py - AIE Ch 2: self-attention by hand, and what a model's size numbers mean
import numpy as np

rng = np.random.default_rng(2)
np.set_printoptions(precision=2, suppress=True)

print('PART A  attention: each token looks back at earlier tokens and decides how much each one matters')
tokens = ['the', 'bank', 'raised', 'interest', 'rates']
D = 8
x = rng.normal(size=(len(tokens), D))                      # one vector per token (random here; learned in a real model)
Wq, Wk, Wv = (rng.normal(size=(D, D)) / np.sqrt(D) for _ in range(3))
Q, K, V = x @ Wq, x @ Wk, x @ Wv                            # query: what am I looking for?  key: what do I offer?  value: what I pass on
scores = Q @ K.T / np.sqrt(D)
scores[np.triu_indices(len(tokens), k=1)] = -np.inf         # causal mask: a token may not look at tokens that come after it
weights = np.exp(scores - scores.max(axis=1, keepdims=True))
weights /= weights.sum(axis=1, keepdims=True)
out = weights @ V
print(f'  {"":>10}' + ''.join(f'{t:>10}' for t in tokens))
for t, row in zip(tokens, weights):
    print(f'  {t:>10}' + ''.join(f'{w:>10.2f}' for w in row))
print('  Each row adds up to 1. The zeros above the diagonal are the mask: nothing can attend to the future.')
print(f'  Output: {out.shape[0]} vectors of size {out.shape[1]}, each one a weighted blend of the values of the tokens before it.')

print('\nPART B  the work attention does grows with the square of the sequence length')
for n in [1_000, 8_000, 128_000]:
    print(f'  context of {n:>7,} tokens -> {n * n:>18,} token pairs per attention layer')

print('\nPART C  counting parameters for a transformer of a given shape')


def parameters(layers, dim, ff_dim, vocab):
    attention = 4 * dim * dim                               # query, key, value and output projections
    feedforward = 2 * dim * ff_dim                          # two linear layers
    embedding = vocab * dim                                 # one vector per token in the vocabulary
    return layers * (attention + feedforward) + embedding


print(f'  {"shape":<46}{"parameters":>13}{"32-bit":>10}{"16-bit":>10}{"4-bit":>9}')
for name, (layers, dim, ff, vocab) in {'small  (12 layers, width 768)': (12, 768, 3072, 50_000), 'medium (32 layers, width 4096)': (32, 4096, 11_008, 32_000),
                                       'large  (80 layers, width 8192)': (80, 8192, 22_016, 32_000)}.items():
    n = parameters(layers, dim, ff, vocab)
    print(f'  {name:<46}{n / 1e9:>11.2f} B{n * 4 / 1e9:>8.1f} GB{n * 2 / 1e9:>8.1f} GB{n * 0.5 / 1e9:>7.1f} GB')
print('  Memory just to hold the weights = parameters x bytes per parameter. The same model needs 8x less at 4 bits than at 32.')
