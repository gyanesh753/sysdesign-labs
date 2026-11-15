# lab2_structured_output.py - AIE Ch 5: getting JSON you can parse: ask nicely, or constrain the sampling
import json

from llm import MODEL, chat

TEXTS = [
    ('Paid Rs 4,200 to Asha Traders on 3 March 2026 for printer ink.', {'vendor': 'Asha Traders', 'amount': 4200, 'date': '2026-03-03'}),
    ('Invoice from Blue Kettle Cafe dated 2026-01-17, total 860 rupees.', {'vendor': 'Blue Kettle Cafe', 'amount': 860, 'date': '2026-01-17'}),
    ('On 12 Feb 2026 we transferred 15,000 to "Northwind Logistics" (freight).', {'vendor': 'Northwind Logistics', 'amount': 15000, 'date': '2026-02-12'}),
    ('Lakshmi Stationers billed us 1,275.50 on the 9th of April 2026.', {'vendor': 'Lakshmi Stationers', 'amount': 1275.5, 'date': '2026-04-09'}),
    ('Receipt: Metro Cabs, 28/05/2026, Rs. 640 (airport drop).', {'vendor': 'Metro Cabs', 'amount': 640, 'date': '2026-05-28'}),
    ('We owe Orbit Hosting 2,999 for the server; bill date June 1, 2026.', {'vendor': 'Orbit Hosting', 'amount': 2999, 'date': '2026-06-01'}),
    ('30 Jan 2026 - "Green Leaf Catering" - lunch for 40 people - 18,400', {'vendor': 'Green Leaf Catering', 'amount': 18400, 'date': '2026-01-30'}),
    ('Paid the electrician (Sharma & Sons) nine hundred rupees on 2026-07-14.', {'vendor': 'Sharma & Sons', 'amount': 900, 'date': '2026-07-14'}),
]
INSTRUCTION = ('Extract the payment from the text as JSON with exactly these keys: "vendor" (string), "amount" (number, no currency symbol or commas), '
               '"date" (string, YYYY-MM-DD).')
SCHEMA = {'type': 'object', 'properties': {'vendor': {'type': 'string'}, 'amount': {'type': 'number'}, 'date': {'type': 'string'}},
          'required': ['vendor', 'amount', 'date']}


def strip_fences(text):
    """Models often wrap JSON in a markdown code block. Remove it before parsing."""
    text = text.strip()
    if text.startswith('```'):
        text = text.split('\n', 1)[1] if '\n' in text else text
        text = text.rsplit('```', 1)[0]
    return text.strip()


def score(build, schema=None, repair=False):
    parsed = right_keys = fields = 0
    first = None
    for text, truth in TEXTS:
        out = chat(build(text), max_tokens=120, schema=schema)
        first = first or out
        try:
            data = json.loads(strip_fences(out) if repair else out)
        except json.JSONDecodeError:
            continue
        parsed += 1
        if isinstance(data, dict) and set(data) == set(truth):
            right_keys += 1
            fields += sum(str(data[k]).strip() == str(truth[k]) or data[k] == truth[k] for k in truth)
    return parsed, right_keys, fields, first


print(f'model: {MODEL}, {len(TEXTS)} texts\n')
print(f'{"approach":<44}{"parses as JSON":>16}{"exact keys":>12}{"fields correct":>16}')
described = lambda t: f'{INSTRUCTION}\n\nText: {t}'
for name, build, schema, repair in [('no format mentioned', lambda t: f'What payment does this text describe?\n\n{t}', None, False),
                                    ('format described in the prompt', described, None, False),
                                    ('format described + repair in code', described, None, True),
                                    ('format described + constrained sampling', described, SCHEMA, False)]:
    try:
        parsed, keys, fields, first = score(build, schema, repair)
    except RuntimeError as e:
        print(f'{name:<44}not available with this model or server ({e})')
        continue
    print(f'{name:<44}{f"{parsed} of {len(TEXTS)}":>16}{f"{keys} of {len(TEXTS)}":>12}{f"{fields} of {len(TEXTS) * 3}":>16}')
    print(f'    first reply: {first[:100]!r}')
print('\nRepairing in code and constraining the sampling both fix the SHAPE of the output. Neither can make the values right.')
