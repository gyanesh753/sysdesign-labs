# lab3_synthesis.py - AIE Ch 8: making training data: templates, checking what was generated, and training on your own output
import random

import numpy as np

random.seed(8)
rng = np.random.default_rng(8)

print('PART A  rule-based synthesis: a few templates and lists multiply into wide coverage')
seed_examples = [('What is 12 plus 7?', '19'), ('What is 30 minus 4?', '26'), ('What is 6 times 5?', '30')]
OPS = {'plus': lambda a, b: a + b, 'minus': lambda a, b: a - b, 'times': lambda a, b: a * b}
PHRASINGS = ['What is {a} {op} {b}?', 'Calculate {a} {op} {b}.', 'A shop has {a} items and the count is {op} {b}. What is the result?', 'Work out {a} {op} {b} and give only the number.']
synthetic = [(p.format(a=a, op=op, b=b), str(fn(a, b))) for p in PHRASINGS for op, fn in OPS.items() for a in range(2, 40, 3) for b in range(2, 40, 5)]
print(f'  {len(seed_examples)} hand-written examples -> {len(synthetic):,} generated ones covering {len(PHRASINGS)} phrasings x {len(OPS)} operations x many numbers')

print('\nPART B  a generator that is sometimes wrong, and a check that catches it')


def careless_generator(question, answer):
    """Stands in for a model writing training answers: fluent, and wrong 8% of the time."""
    return answer if random.random() > 0.08 else str(int(answer) + random.choice([-10, -1, 1, 10]))


generated = [(q, careless_generator(q, a), a) for q, a in synthetic]
wrong = sum(g != truth for _, g, truth in generated)
print(f'  {wrong} of {len(generated):,} generated answers are wrong ({wrong / len(generated):.1%}), and they look just as confident as the right ones')


def verify(question, answer):
    """Functional check: recompute the answer from the question instead of trusting the generator."""
    words = question.replace('?', '').replace('.', '').split()
    numbers = [int(w) for w in words if w.isdigit()]
    op = next(w for w in words if w in OPS)
    return str(OPS[op](numbers[0], numbers[1])) == answer


kept = [(q, g) for q, g, _ in generated if verify(q, g)]
still_wrong = sum(g != truth for (q, g), (_, _, truth) in zip(kept, [x for x in generated if verify(x[0], x[1])]))
print(f'  after verification: {len(kept):,} kept, {len(generated) - len(kept)} rejected, {still_wrong} wrong answers remaining')
print('  This works because arithmetic can be checked by running it. For open-ended text you need a judge, and judges make mistakes too.')

print('\nPART C  training each new model only on the previous model\'s output')
real = rng.normal(0, 1, 2_000)
print(f'  {"generation":>11}{"spread of the data":>20}{"share of rare cases (beyond 2)":>32}')
data = real
for generation in range(9):
    if generation in (0, 1, 2, 4, 8):
        print(f'  {generation:>11}{data.std():>20.2f}{(np.abs(data) > 2).mean():>32.1%}')
    mean, std = data.mean(), data.std()
    samples = rng.normal(mean, std, 2_000)
    data = samples[np.abs(samples - mean) < 2.2 * std]         # a model favours typical outputs and under-produces unusual ones
print('  Each generation loses a little of the unusual material, and the losses compound until the rare cases are gone.')
print('  Mixing real data back in at every step is what prevents this.')
