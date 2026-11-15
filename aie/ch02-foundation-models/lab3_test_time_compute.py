# lab3_test_time_compute.py - AIE Ch 2: spending more computation per question instead of using a bigger model
import numpy as np

rng = np.random.default_rng(2)
QUESTIONS = 20_000

def vote_accuracy(n, probabilities):
    """Draw n answers per question (answer 0 is the right one) and take the most common, breaking ties at random."""
    draws = rng.choice(len(probabilities), size=(QUESTIONS, n), p=probabilities)
    counts = np.stack([(draws == a).sum(axis=1) for a in range(len(probabilities))], axis=1)
    counts = counts + rng.random(counts.shape) * 0.5          # random tie-break
    return (counts.argmax(axis=1) == 0).mean()


print('PART A  ask the same question several times and take the most common answer')
print('  A model answers a maths question correctly 60% of the time. When wrong, it gives one of four wrong answers at random.')
print(f'  {"samples":>8}{"accuracy":>10}{"cost":>7}')
for n in [1, 3, 5, 11, 25]:
    print(f'  {n:>8}{vote_accuracy(n, [0.6, 0.1, 0.1, 0.1, 0.1]):>10.1%}{n:>6}x')

print('\nPART B  the same trick does nothing when the model is wrong in a consistent way')
print('  Now the model prefers one particular wrong answer: right 35% of the time, the same wrong answer 45% of the time.')
print(f'  {"samples":>8}{"accuracy":>10}')
for n in [1, 5, 25]:
    print(f'  {n:>8}{vote_accuracy(n, [0.35, 0.45, 0.1, 0.05, 0.05]):>10.1%}')
print('  Voting amplifies whatever the model leans towards. If it leans wrong, more samples make it more wrong.')

print('\nPART C  generate several candidates and let a checker choose')
print('  Each candidate program passes the tests 30% of the time. A test suite tells us which ones pass.')
print(f'  {"candidates":>11}{"at least one passes":>22}')
for n in [1, 3, 10, 30]:
    print(f'  {n:>11}{((rng.random((QUESTIONS, n)) < 0.3).any(axis=1)).mean():>22.1%}   (theory {1 - 0.7 ** n:.1%})')
print('  With a reliable way to check answers, many cheap attempts can beat one expensive one.')
