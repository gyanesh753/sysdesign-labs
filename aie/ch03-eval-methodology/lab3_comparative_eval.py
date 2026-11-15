# lab3_comparative_eval.py - AIE Ch 3: ranking models from head-to-head votes, and how a biased judge distorts it
import itertools

import numpy as np

rng = np.random.default_rng(3)
MODELS = ['A', 'B', 'C', 'D', 'E', 'F']
TRUE_SKILL = np.array([1250, 1180, 1100, 1090, 1000, 880])       # hidden: what we are trying to recover


def win_probability(r_a, r_b):
    return 1 / (1 + 10 ** ((r_b - r_a) / 400))


def fit_ratings(matches):
    """Fit one rating per model to ALL the votes at once (the Bradley-Terry model, which Elo-style leaderboards are built on)."""
    m = len(MODELS)
    wins, games = np.zeros(m), np.zeros((m, m))
    for a, b, a_won in matches:
        wins[a] += a_won
        wins[b] += 1 - a_won
        games[a, b] += 1
        games[b, a] += 1
    strength = np.ones(m)
    for _ in range(300):
        denom = (games / (strength[:, None] + strength[None, :])).sum(axis=1)
        strength = np.maximum(wins, 0.5) / denom
        strength /= np.exp(np.log(strength).mean())
    return 1000 + 400 * np.log10(strength)


def play(n, first_position_bonus=0.0, randomize_order=True):
    matches = []
    for _ in range(n):
        a, b = rng.choice(len(MODELS), 2, replace=False)
        if not randomize_order and a > b:
            a, b = b, a                                           # the lower-numbered model is always shown first
        p = win_probability(TRUE_SKILL[a], TRUE_SKILL[b]) + first_position_bonus
        matches.append((a, b, float(rng.random() < min(p, 1))))
    return matches


print('PART A  how many votes until the ranking is right?')
print(f'  true order: {" > ".join(MODELS)}')
for n in [30, 300, 3_000, 30_000]:
    ratings = fit_ratings(play(n))
    order = [MODELS[i] for i in np.argsort(-ratings)]
    wrong = sum(1 for x, y in itertools.combinations(range(len(MODELS)), 2) if (ratings[x] < ratings[y]))
    print(f'  {n:>6,} votes: {" > ".join(order)}   ({wrong} of 15 pairs in the wrong order)')
print('  C and D are nearly equal in skill, so they take the longest to separate.')

print('\nPART B  comparisons scale badly')
for m in [6, 20, 100]:
    print(f'  {m:>3} models -> {m * (m - 1) // 2:>5,} distinct pairs to compare')

print('\nPART C  a judge that favours whichever answer it sees first')
print('  E and F are the two weakest models. Suppose every comparison lists the models in a fixed order.')
for label, bonus, randomize in [('fair judge', 0.0, True), ('biased judge, fixed order', 0.12, False), ('biased judge, order randomized', 0.12, True)]:
    ratings = fit_ratings(play(30_000, bonus, randomize))
    order = [MODELS[i] for i in np.argsort(-ratings)]
    print(f'  {label:<32} gap between A and F: {ratings[0] - ratings[5]:>5.0f} points   order: {" > ".join(order)}')
print('  With a fixed order the bias always helps the same models and stretches the gaps. Randomizing which answer')
print('  comes first spreads the bias evenly, and the measured gaps return to about the fair value.')

print('\nPART D  a ranking says who is better, not who is good enough')
print(f'  Model A wins {win_probability(TRUE_SKILL[0], TRUE_SKILL[5]):.0%} of its comparisons with F. That is all the rating tells you.')
print('  If every model answers only half of your questions correctly, the top of the leaderboard is still not usable.')
