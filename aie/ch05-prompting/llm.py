# llm.py - shared by the chapter 5 labs: one function that calls whichever chat model Ollama has
import requests

HOST = 'http://localhost:11434'
_models = [m['name'] for m in requests.get(f'{HOST}/api/tags', timeout=5).json()['models']]
MODEL = next(m for m in _models if 'embed' not in m)


def chat(user, system=None, temperature=0.0, max_tokens=80, schema=None):
    messages = ([{'role': 'system', 'content': system}] if system else []) + [{'role': 'user', 'content': user}]
    body = {'model': MODEL, 'messages': messages, 'stream': False, 'think': False, 'options': {'temperature': temperature, 'num_predict': max_tokens}}
    if schema:
        body['format'] = schema                      # constrained sampling: only tokens that keep the output valid are allowed
    r = requests.post(f'{HOST}/api/chat', json=body, timeout=300)
    if r.status_code != 200:                         # models without a thinking mode reject the flag
        body.pop('think')
        r = requests.post(f'{HOST}/api/chat', json=body, timeout=300)
    data = r.json()
    if 'message' not in data:
        raise RuntimeError(data.get('error', 'the model server returned no message'))
    return data['message']['content'].strip()
