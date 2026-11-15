# lab3_first_call.py - AIE Ch 1: a model as a service: one HTTP call in, text out, and tokens are the unit of everything
import time

import requests

HOST = 'http://localhost:11434'
models = [m['name'] for m in requests.get(f'{HOST}/api/tags', timeout=5).json()['models']]
MODEL = next(m for m in models if 'embed' not in m)             # any chat model you have pulled


def chat(prompt, temperature=0.0, max_tokens=60):
    body = {'model': MODEL, 'messages': [{'role': 'user', 'content': prompt}], 'stream': False, 'think': False,
            'options': {'temperature': temperature, 'num_predict': max_tokens}}
    start = time.perf_counter()
    r = requests.post(f'{HOST}/api/chat', json=body, timeout=300)
    if r.status_code != 200:                                    # models without a thinking mode reject the flag
        body.pop('think')
        r = requests.post(f'{HOST}/api/chat', json=body, timeout=300)
    d = r.json()
    return d['message']['content'].strip(), d.get('prompt_eval_count', 0), d.get('eval_count', 0), time.perf_counter() - start


print(f'model: {MODEL}\n')
chat('Say OK.')                                                 # the first call loads the model into memory

print('PART A  the same prompt, temperature 0, twice')
prompt = 'Suggest one name for a bakery. Reply with the name only.'
answers = [chat(prompt, temperature=0)[0] for _ in range(2)]
print(f'  {answers[0]!r} and {answers[1]!r}  ->  {"identical" if answers[0] == answers[1] else "different"}')

print('\nPART B  the same prompt, temperature 1.3, five times')
varied = [chat(prompt, temperature=1.3)[0] for _ in range(5)]
print(f'  {varied}')
print(f'  {len(set(varied))} distinct answers out of 5: the model samples from a distribution, it does not look anything up')

print('\nPART C  what you pay for: tokens in, tokens out')
print(f'  {"prompt":<46}{"tokens in":>10}{"tokens out":>11}{"seconds":>9}')
for label, p in [('one short question', 'What is the capital of France? One word.'),
                 ('the same question preceded by 300 words', 'Background: ' + 'the quick brown fox jumps over the lazy dog. ' * 34 + '\nWhat is the capital of France? One word.'),
                 ('a request for a longer answer', 'List ten European capitals, one per line.')]:
    text, tin, tout, seconds = chat(p, max_tokens=120)
    print(f'  {label:<46}{tin:>10}{tout:>11}{seconds:>9.2f}')

print('\nPART D  tokens are not words')
for label, p in [('English', 'Where is the nearest railway station?'), ('Hindi', 'सबसे नज़दीकी रेलवे स्टेशन कहाँ है?')]:
    _, tin, _, _ = chat(p, max_tokens=1)
    print(f'  {label:<8} {len(p.split())} words -> {tin} prompt tokens (including the chat template)')
