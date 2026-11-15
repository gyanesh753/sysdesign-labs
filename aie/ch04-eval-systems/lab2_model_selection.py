# lab2_model_selection.py - AIE Ch 4: choosing a model: hard requirements first, then the trade-offs, then the bill
# All figures below are invented for the exercise. Replace them with your own measurements.
CANDIDATES = [
    # name,                 quality on our eval, p95 latency s, $ per million tokens, can run on our servers, licence allows commercial use
    ('large API model',            0.91, 2.8, 12.00, False, True),
    ('mid-size API model',         0.86, 1.1,  2.00, False, True),
    ('small API model',            0.78, 0.5,  0.30, False, True),
    ('open model, 70B, self-host', 0.87, 2.2,  None, True,  True),
    ('open model, 8B, self-host',  0.80, 0.6,  None, True,  True),
    ('research model, 30B',        0.89, 1.5,  None, True,  False),
]
REQUIRE = {'min_quality': 0.80, 'max_latency': 2.5}

print('STEP 1  hard requirements remove candidates before any trade-off is discussed')
shortlist = []
for name, quality, latency, price, self_host, commercial in CANDIDATES:
    reasons = []
    if not commercial:
        reasons.append('licence forbids commercial use')
    if quality < REQUIRE['min_quality']:
        reasons.append(f'quality {quality:.2f} is below {REQUIRE["min_quality"]}')
    if latency > REQUIRE['max_latency']:
        reasons.append(f'latency {latency}s is above {REQUIRE["max_latency"]}s')
    print(f'  {name:<28}{"kept" if not reasons else "out: " + "; ".join(reasons)}')
    if not reasons:
        shortlist.append((name, quality, latency, price, self_host))

print('\nSTEP 2  among those left, drop any model that another one beats on both quality and latency')
for name, quality, latency, price, self_host in shortlist:
    beaten_by = [n for n, q, l, _, _ in shortlist if q >= quality and l <= latency and (q, l) != (quality, latency)]
    print(f'  {name:<28}quality {quality:.2f}  latency {latency}s  ' + (f'dominated by {beaten_by[0]}' if beaten_by else 'on the frontier'))

print('\nSTEP 3  what does it cost per month? API price per token against a fixed server bill')
API_PRICE = 2.00                     # dollars per million tokens, mid-size API model
SERVER = 6_500                       # dollars per month for GPUs and the share of an engineer to run them
TOKENS_PER_REQUEST = 1_500
print(f'  {"requests per day":>17}{"API bill":>12}{"self-hosted":>13}   cheaper')
for per_day in [1_000, 10_000, 50_000, 100_000, 500_000]:
    api = per_day * 30 * TOKENS_PER_REQUEST / 1e6 * API_PRICE
    print(f'  {per_day:>17,}{api:>11,.0f}${SERVER:>12,}$   {"API" if api < SERVER else "self-hosting"}')
breakeven = SERVER / (30 * TOKENS_PER_REQUEST / 1e6 * API_PRICE)
print(f'  Break-even at about {breakeven:,.0f} requests a day. Below that, paying per token is cheaper; above it, owning the capacity is.')
print('  The comparison leaves out what is hard to price: control, privacy, and the engineering time self-hosting takes.')
