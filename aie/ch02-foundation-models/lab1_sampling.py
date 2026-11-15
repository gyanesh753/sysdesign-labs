# lab1_sampling.py - AIE Ch 2: from a model's raw scores to a chosen token: temperature, top-k and top-p
import numpy as np

rng = np.random.default_rng(2)

# Pretend the prompt is "My favourite colour is" and the model scored these candidate next tokens.
TOKENS = ['blue', 'green', 'red', 'purple', 'orange', 'yellow', 'teal', 'banana', 'the', 'seven']
LOGITS = np.array([4.0, 3.4, 3.1, 2.2, 1.6, 1.3, 0.4, -1.0, -1.5, -3.0])


def softmax(logits, temperature=1.0):
    z = logits / temperature
    z = z - z.max()
    p = np.exp(z)
    return p / p.sum()


def show(p):
    return '  '.join(f'{t} {x:.0%}' for t, x in zip(TOKENS, p) if x >= 0.005)


print('PART A  logits are arbitrary scores; softmax turns them into probabilities that add up to 1')
print(f'  {show(softmax(LOGITS))}')

print('\nPART B  temperature divides the logits before softmax')
print(f'  {"temperature":>12}  {"top token":>10}  {"chance of a nonsense token":>28}  {"distinct tokens in 1,000 samples":>34}')
for t in [0.2, 0.7, 1.0, 1.5, 3.0]:
    p = softmax(LOGITS, t)
    samples = rng.choice(len(TOKENS), 1_000, p=p)
    print(f'  {t:>12}  {p[0]:>10.0%}  {p[7:].sum():>28.2%}  {len(set(samples)):>34}')
print('  Low temperature: nearly always "blue". High temperature: more variety, and "banana" starts to appear.')

print('\nPART C  top-k keeps only the k highest-scoring tokens, then renormalizes')
for k in [1, 3, 5]:
    p = softmax(LOGITS)
    keep = np.argsort(-p)[:k]
    q = np.zeros_like(p)
    q[keep] = p[keep] / p[keep].sum()
    print(f'  k={k}: {show(q)}')

print('\nPART D  top-p keeps the smallest set of tokens whose probabilities add up to p')
for name, logits in [('a confident model   ', np.array([8.0, 3.4, 3.1, 2.2, 1.6, 1.3, 0.4, -1.0, -1.5, -3.0])), ('an unsure model     ', LOGITS * 0.3)]:
    p = softmax(logits)
    order = np.argsort(-p)
    kept = order[:int(np.searchsorted(np.cumsum(p[order]), 0.9)) + 1]
    print(f'  {name} top-p 0.9 keeps {len(kept)} token(s): {", ".join(TOKENS[i] for i in kept)}')
print('  top-k always keeps the same number. top-p adapts: few candidates when the model is sure, many when it is not.')

print('\nPART E  log probabilities: how sure was the model of a whole answer?')
p = softmax(LOGITS)
for answer in [['blue'], ['banana']]:
    logprob = sum(np.log(p[TOKENS.index(t)]) for t in answer)
    print(f'  "{answer[0]}": probability {np.exp(logprob):.3%}, log probability {logprob:.2f}')
print('  Probabilities of long answers get vanishingly small, so they are added as logs instead of multiplied.')
