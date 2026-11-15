# lab1_latency_metrics.py - AIE Ch 9: time to first token, time per output token and throughput, measured on a real model
import json
import random
import time

import requests

HOST = 'http://localhost:11434'
MODEL = next(m['name'] for m in requests.get(f'{HOST}/api/tags', timeout=5).json()['models'] if 'embed' not in m['name'])


def stream(prompt, max_tokens):
    """Send one request and record when each piece of the answer arrives."""
    body = {'model': MODEL, 'messages': [{'role': 'user', 'content': prompt}], 'stream': True, 'think': False,
            'options': {'temperature': 0, 'num_predict': max_tokens}}
    start = time.perf_counter()
    r = requests.post(f'{HOST}/api/chat', json=body, stream=True, timeout=600)
    if r.status_code != 200:
        body.pop('think')
        start = time.perf_counter()
        r = requests.post(f'{HOST}/api/chat', json=body, stream=True, timeout=600)
    arrivals, final = [], {}
    for line in r.iter_lines():
        if not line:
            continue
        chunk = json.loads(line)
        if chunk.get('message', {}).get('content'):
            arrivals.append(time.perf_counter() - start)
        if chunk.get('done'):
            final = chunk
    ttft = arrivals[0]
    out_tokens = final.get('eval_count', len(arrivals))
    tpot = (arrivals[-1] - arrivals[0]) / max(1, out_tokens - 1)
    return {'in': final.get('prompt_eval_count', 0), 'out': out_tokens, 'ttft': ttft, 'tpot': tpot, 'total': arrivals[-1]}


stream('Say OK.', 5)                                         # load the model before measuring anything
# A long prompt that is different on every run, so the server cannot have seen it before.
FILLER = f'Report number {random.randrange(10**9)}. ' + 'The quarterly report covers revenue, costs, staffing and the outlook for next year. ' * 60
LONG = FILLER + '\nIn one word, what kind of document is described above?'
CASES = [('short prompt, short answer', 'Name one primary colour. One word.', 10),
         ('short prompt, long answer', 'Write a 150-word description of a lighthouse.', 260),
         ('long prompt, first time', LONG, 10),
         ('the same long prompt again', LONG, 10)]

print(f'model: {MODEL}\n')
print(f'{"request":<28}{"tokens in":>10}{"tokens out":>11}{"first token after":>19}{"per output token":>18}{"total":>9}{"tokens/s":>10}')
rows = []
for label, prompt, limit in CASES:
    m = stream(prompt, limit)
    rows.append(m)
    many = m['out'] > 1                                       # per-token figures mean nothing for a one-token answer
    tpot = f'{m["tpot"] * 1000:.1f} ms' if many else '-'
    rate = f'{m["out"] / (m["total"] - m["ttft"]):.0f}' if many else '-'
    print(f'{label:<28}{m["in"]:>10}{m["out"]:>11}{m["ttft"] * 1000:>16.0f} ms{tpot:>18}{m["total"]:>8.2f}s{rate:>10}')

print('\nWhat to read from this:')
print(f'  - The long answer takes {rows[1]["total"] / rows[0]["total"]:.0f}x as long in total as the short one. Its first token arrives about as fast.')
print(f'  - The long prompt delays the FIRST token ({rows[2]["ttft"] * 1000:.0f} ms against {rows[0]["ttft"] * 1000:.0f} ms): the model has to read everything before it can start.')
print(f'  - Sent a second time, the same long prompt starts answering in {rows[3]["ttft"] * 1000:.0f} ms. The server kept its work on that prompt: prompt caching.')
print('  - Input length drives time to first token. Output length drives total time. They are tuned separately.')
