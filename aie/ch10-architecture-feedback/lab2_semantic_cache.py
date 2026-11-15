# lab2_semantic_cache.py - AIE Ch 10: a semantic cache answers "similar" questions from memory. How similar is similar enough?
import numpy as np
import requests

# Pairs that mean the same thing: the cached answer to the first is a correct answer to the second.
SAME = [
    ('How do I reset my password?', 'I forgot my password, how can I change it?'),
    ('What are your opening hours?', 'When are you open?'),
    ('How can I cancel my subscription?', 'I want to stop my subscription. What do I do?'),
    ('Where is my order?', 'Can you tell me the status of my order?'),
    ('Do you ship to Canada?', 'Is delivery to Canada available?'),
    ('How do I download my invoice?', 'Where can I get a copy of my invoice?'),
    ('Can I change my delivery address?', 'How do I update the address my order is sent to?'),
    ('How do I contact support?', 'What is the best way to reach customer service?'),
]
# Pairs that look alike and need DIFFERENT answers: serving the cached answer would be wrong.
DIFFERENT = [
    ('How can I cancel my subscription?', 'How can I cancel my order?'),
    ('How do I reset my password?', 'How do I reset my two-factor authentication?'),
    ('Do you ship to Canada?', 'Do you ship to Kenya?'),
    ('What is the price of the basic plan?', 'What is the price of the premium plan?'),
    ('How do I upgrade my plan?', 'How do I downgrade my plan?'),
    ('Is the app available on Android?', 'Is the app available on iPhone?'),
    ('Can I pay by credit card?', 'Can I pay by bank transfer?'),
    ('How do I add a user to my team?', 'How do I remove a user from my team?'),
]


def embed(texts):
    r = requests.post('http://localhost:11434/api/embed', json={'model': 'nomic-embed-text', 'input': [f'clustering: {t}' for t in texts]}, timeout=120)
    v = np.array(r.json()['embeddings'])
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def similarities(pairs):
    a, b = embed([p[0] for p in pairs]), embed([p[1] for p in pairs])
    return (a * b).sum(axis=1)


same, different = similarities(SAME), similarities(DIFFERENT)
print(f'similarity of same-meaning pairs:      lowest {same.min():.2f}, average {same.mean():.2f}, highest {same.max():.2f}')
print(f'similarity of look-alike pairs:        lowest {different.min():.2f}, average {different.mean():.2f}, highest {different.max():.2f}\n')
print(f'{"cache threshold":>16}{"same-meaning questions served from cache":>44}{"look-alike questions given a WRONG cached answer":>52}')
for threshold in [0.98, 0.95, 0.90, 0.85, 0.80, 0.70]:
    print(f'{threshold:>16.2f}{(same >= threshold).mean():>44.0%}{(different >= threshold).mean():>52.0%}')
print('\nThe most confusable look-alike pairs:')
for i in np.argsort(-different)[:3]:
    print(f'  {different[i]:.2f}  "{DIFFERENT[i][0]}"  vs  "{DIFFERENT[i][1]}"')
print('\nIf the two groups overlap, no threshold gives many correct hits and no wrong ones. A wrong hit is worse than a miss:')
print('the user gets a confident answer to a question they did not ask.')
