# lab3_feedback_signals.py - AIE Ch 10: reading feedback out of conversations, and three ways it misleads
import random

random.seed(10)

print('PART A  most users never click a rating, but their behaviour says a lot')
CORRECTIONS = ('no,', 'that is wrong', "that's not", 'i meant', 'not what i asked')
PRAISE = ('thanks', 'thank you', 'perfect', 'great')


def simulate_conversation(quality):
    """quality = chance that the assistant's answer is good. Returns the events a product would log."""
    good = random.random() < quality
    events = []
    if good:
        events.append(random.choice(['user: thanks, that works', 'user: perfect', 'action: copied answer', 'action: copied answer', 'user: next question']))
    else:
        events.append(random.choice(['user: no, i meant the other account', 'user: that is wrong', 'action: regenerate', 'action: stopped generation early', 'action: left']))
    if random.random() < 0.03:                                    # only a few percent ever press a button
        events.append('rating: up' if good or random.random() < 0.3 else 'rating: down')     # unhappy users mostly just leave
    return good, events


def signals(events):
    text = ' '.join(events).lower()
    negative = any(c in text for c in CORRECTIONS) or 'regenerate' in text or 'stopped generation early' in text or 'action: left' in text
    positive = any(p in text for p in PRAISE) or 'copied answer' in text
    return positive, negative


print(f'  {"version":<12}{"true share of good answers":>28}{"thumbs-up rate":>16}{"ratings received":>18}{"implicit satisfaction":>23}')
for version, quality in [('version 1', 0.70), ('version 2', 0.80)]:
    conversations = [simulate_conversation(quality) for _ in range(20_000)]
    truth = sum(g for g, _ in conversations) / len(conversations)
    ratings = [e for _, ev in conversations for e in ev if e.startswith('rating')]
    up = sum(r == 'rating: up' for r in ratings) / len(ratings)
    judged = [signals(ev) for _, ev in conversations]
    implicit = sum(p for p, n in judged) / max(1, sum(p or n for p, n in judged))
    print(f'  {version:<12}{truth:>28.1%}{up:>16.1%}{len(ratings):>18,}{implicit:>23.1%}')
print('  Thumbs come from 3% of conversations and flatter both versions, because unhappy users rarely bother to rate.')
print('  Signals read from behaviour cover far more conversations, land nearer the truth, and separate the two versions clearly.')

print('\nPART B  position bias: people tend to pick whichever answer is shown first')
TRIALS = 50_000
prefer_first = 0.60                                                # the two answers are equally good; 60% click the first anyway
fixed = sum(random.random() < prefer_first for _ in range(TRIALS)) / TRIALS
randomized = sum((random.random() < prefer_first) == (random.random() < 0.5) for _ in range(TRIALS)) / TRIALS
print(f'  model A always shown first:   A "wins" {fixed:.1%} of comparisons')
print(f'  order randomized each time:   A wins {randomized:.1%}')
print('  The models are identical. With a fixed order, the layout of the page decided the winner.')

print('\nPART C  a degenerate feedback loop: showing what was clicked, and getting clicked because it was shown')
ITEMS = 20


def run(explore):
    clicks, shown_count = [1] * ITEMS, [0] * ITEMS                 # every item is equally good in truth
    for _ in range(20_000):
        if random.random() < explore:
            shown = random.randrange(ITEMS)                        # sometimes show something at random
        else:
            shown = max(range(ITEMS), key=lambda i: clicks[i])     # otherwise show the most-clicked item
        shown_count[shown] += 1
        if random.random() < 0.3:
            clicks[shown] += 1
    return max(clicks) / sum(clicks), sum(n >= 100 for n in shown_count)


for label, explore in [('always show the most-clicked item', 0.0), ('show a random item 20% of the time', 0.2)]:
    share, tested = run(explore)
    print(f'  {label + ":":<40}top item gets {share:.0%} of clicks; items shown often enough to judge: {tested} of {ITEMS}')
print('  All twenty items are equally good. Without exploration the system never finds that out: one early click decides')
print('  everything, and the data it collects afterwards can only confirm the choice.')
