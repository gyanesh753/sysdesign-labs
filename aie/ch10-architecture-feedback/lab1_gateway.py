# lab1_gateway.py - AIE Ch 10: adding the pieces around a model one at a time: guardrail, router, cache, fallback
# Prices, latencies and failure rates are invented for the exercise.
import random
import re

random.seed(10)

print('PART A  an input guardrail: mask personal data before it leaves your system, restore it in the reply')
PATTERNS = {'EMAIL': r'[\w.+-]+@[\w-]+\.[\w.]+', 'PHONE': r'\b\d{10}\b'}


def mask(text):
    vault = {}
    for kind, pattern in PATTERNS.items():
        for n, match in enumerate(re.findall(pattern, text), 1):
            placeholder = f'[{kind}_{n}]'
            vault[placeholder] = match
            text = text.replace(match, placeholder)
    return text, vault


def unmask(text, vault):
    for placeholder, original in vault.items():
        text = text.replace(placeholder, original)
    return text


user = 'Please send the invoice to priya.k@example.com and call me on 9876543210 if it bounces.'
masked, vault = mask(user)
model_reply = f'Sure. I will send the invoice to {list(vault)[0]} and call {list(vault)[1]} if it bounces.'       # what an external model would return
print(f'  user wrote:        {user}')
print(f'  sent to the model: {masked}')
print(f'  shown to the user: {unmask(model_reply, vault)}')

print('\nPART B  a router and a cache on 20,000 requests')
MODELS = {'small': {'cost': 0.0004, 'latency': 0.4}, 'large': {'cost': 0.0120, 'latency': 2.1}}
QUESTIONS = [(f'question {i}', 'simple' if i % 10 < 7 else 'hard') for i in range(600)]     # 70% of distinct questions are simple
weights = [1 / (i + 1) ** 1.1 for i in range(len(QUESTIONS))]                               # a few questions are asked very often
traffic = random.choices(QUESTIONS, weights, k=20_000)


def run(use_router, use_cache):
    cost = latency = hits = 0
    cache = set()
    for question, difficulty in traffic:
        if use_cache and question in cache:
            hits += 1
            latency += 0.02                                    # a cache lookup
            continue
        model = MODELS['small'] if use_router and difficulty == 'simple' else MODELS['large']
        if use_router:
            cost += 0.00002                                    # the intent classifier is a tiny model, but not free
            latency += 0.03
        cost += model['cost']
        latency += model['latency']
        cache.add(question)
    return cost, latency / len(traffic), hits / len(traffic)


print(f'  {"configuration":<34}{"total cost":>12}{"average latency":>18}{"served from cache":>20}')
for label, router, cache in [('every request to the large model', False, False), ('+ router (simple -> small model)', True, False),
                             ('+ exact cache', False, True), ('+ router and cache', True, True)]:
    cost, latency, hits = run(router, cache)
    print(f'  {label:<34}{cost:>11.2f}${latency:>16.2f} s{hits:>20.0%}')

print('\nPART C  a gateway can fall back to a second provider when the first one fails')
TRIALS = 100_000
primary_fail, backup_fail = 0.03, 0.05
alone = sum(random.random() > primary_fail for _ in range(TRIALS)) / TRIALS
with_fallback = sum(random.random() > primary_fail or random.random() > backup_fail for _ in range(TRIALS)) / TRIALS
print(f'  primary provider alone: {alone:.2%} of requests succeed   with a fallback: {with_fallback:.2%}')
print(f'  Failures drop from about {(1 - alone) * 1000:.0f} in a thousand to about {(1 - with_fallback) * 1000:.1f} in a thousand.')
