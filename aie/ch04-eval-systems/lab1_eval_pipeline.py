# lab1_eval_pipeline.py - AIE Ch 4: slices, a misleading average, and how much data a comparison needs
import numpy as np

rng = np.random.default_rng(4)

print('PART A  two versions of a support bot, scored on the same kind of questions')
# Each tuple: (questions answered, correct) for an easy slice (password resets) and a hard slice (billing disputes).
results = {'version 1': {'easy': (800, 720), 'hard': (200, 100)},
           'version 2': {'easy': (300, 279), 'hard': (700, 385)}}
print(f'  {"":<11}{"easy questions":>18}{"hard questions":>18}{"overall":>12}')
for name, r in results.items():
    easy, hard = r['easy'], r['hard']
    overall = (easy[1] + hard[1]) / (easy[0] + hard[0])
    print(f'  {name:<11}{f"{easy[1] / easy[0]:.0%} of {easy[0]}":>18}{f"{hard[1] / hard[0]:.0%} of {hard[0]}":>18}{overall:>12.0%}')
print('  Version 2 is better on easy questions AND on hard questions, yet worse overall.')
print('  It was simply tested on many more hard questions. Always look at the slices, and at how many examples each has.')

print('\nPART B  is a 3-point difference real? Bootstrap the test set and see')


def bootstrap_interval(correct, resamples=2_000):
    means = rng.choice(correct, size=(resamples, len(correct))).mean(axis=1)
    return np.percentile(means, [2.5, 97.5])


print(f'  {"test set size":>14}{"model A":>26}{"model B":>26}   can you tell them apart?')
for n in [50, 200, 1_000, 5_000]:
    a = rng.random(n) < 0.80                                  # truly 80% accurate
    b = rng.random(n) < 0.83                                  # truly 83% accurate
    (a_lo, a_hi), (b_lo, b_hi) = bootstrap_interval(a), bootstrap_interval(b)
    verdict = 'yes' if b_lo > a_hi else 'no, the ranges overlap'
    print(f'  {n:>14,}{f"{a.mean():.1%} ({a_lo:.1%} to {a_hi:.1%})":>26}{f"{b.mean():.1%} ({b_lo:.1%} to {b_hi:.1%})":>26}   {verdict}')

print('\nPART C  a rule of thumb: the smaller the difference you care about, the more examples you need')
print(f'  {"difference to detect":>21}{"examples needed (roughly)":>28}')
for diff in [0.30, 0.10, 0.03, 0.01]:
    p = 0.8
    n = int(np.ceil(2 * (1.96 + 0.84) ** 2 * p * (1 - p) / diff ** 2))   # two-sample comparison, 80% power, 5% significance
    print(f'  {diff:>20.0%} {n:>27,}')
print('  Ten times smaller difference, a hundred times more data.')
