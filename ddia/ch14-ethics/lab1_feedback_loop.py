# lab1_feedback_loop.py - DDIA Ch 14: a system that acts on its own predictions can end up confirming them
import numpy as np

rng = np.random.default_rng(14)
INSPECTORS, ROUNDS = 100, 25
TRUE_RATE = np.array([0.10, 0.10])          # two districts with EXACTLY the same real rate of violations per inspection


def simulate(rule):
    share = np.array([0.55, 0.45])          # the starting data happens to be slightly lopsided
    history = []
    for _ in range(ROUNDS):
        sent = np.round(share * INSPECTORS).astype(int)
        found = rng.binomial(sent * 20, TRUE_RATE)              # you only find violations where you look
        if rule == 'follow the counts':
            score = found.astype(float) ** 2                    # "district A had more violations, so it needs more attention"
        else:
            score = found / np.maximum(sent, 1)                 # violations per inspector sent: corrects for where we looked
        share = score / score.sum() if score.sum() else np.array([0.5, 0.5])
        share = np.clip(share, 0.02, 0.98)
        history.append((sent, found))
    return history


for rule, label in [('follow the counts', 'RULE 1  send inspectors where the most violations were recorded'),
                    ('follow the rate', 'RULE 2  send inspectors where the most violations were found PER INSPECTOR')]:
    print(label)
    print(f'  {"round":>5}{"inspectors A / B":>20}{"violations recorded A / B":>30}')
    history = simulate(rule)
    for r in [0, 1, 2, 4, 8, 16, 24]:
        sent, found = history[r]
        print(f'  {r + 1:>5}{f"{sent[0]} / {sent[1]}":>20}{f"{found[0]} / {found[1]}":>30}')
    sent, found = history[-1]
    print(f'  after {ROUNDS} rounds district A gets {sent[0]}% of the inspectors and {found[0] / max(found.sum(), 1):.0%} of all recorded violations\n')
print('Both districts are identical. Under rule 1 the records "prove" that district A is the problem,')
print('because the records measure where the system looked, not what is true.')
