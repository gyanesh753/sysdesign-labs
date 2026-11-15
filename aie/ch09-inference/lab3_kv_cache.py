# lab3_kv_cache.py - AIE Ch 9: why generation reuses its earlier work, what that costs in memory, and what prompt caching saves
print('PART A  attention work when generating tokens one at a time')
print('  Each new token attends to every token before it. Without a cache, the model recomputes everything for all')
print('  earlier tokens at every step. With a cache of keys and values, it computes only what the new token needs.')
print(f'  {"tokens generated":>17}{"token pairs, no cache":>24}{"token pairs, with cache":>26}{"saving":>9}')
PROMPT = 500
for n in [10, 100, 1_000]:
    no_cache = sum((PROMPT + i) ** 2 for i in range(1, n + 1))        # redo the whole sequence each step
    cached = PROMPT ** 2 + sum(PROMPT + i for i in range(1, n + 1))    # read the prompt once, then one row per new token
    print(f'  {n:>17,}{no_cache:>24,}{cached:>26,}{no_cache / cached:>8.0f}x')

print('\nPART B  the cache has to be stored: 2 x layers x width x tokens x bytes, per sequence in the batch')


def kv_cache_gb(layers, width, tokens, batch, bytes_per_value=2):
    return 2 * layers * width * tokens * batch * bytes_per_value / 1e9


print(f'  {"model shape":<28}{"context":>10}{"batch":>7}{"cache size":>13}')
for name, layers, width in [('32 layers, width 4,096', 32, 4_096), ('80 layers, width 8,192', 80, 8_192)]:
    for tokens, batch in [(2_000, 1), (32_000, 1), (32_000, 16)]:
        print(f'  {name:<28}{tokens:>10,}{batch:>7}{kv_cache_gb(layers, width, tokens, batch):>10.1f} GB')
print('  Long contexts and large batches can make the cache bigger than the model itself. This is what limits how many')
print('  requests one accelerator can serve at once.')

print('\nPART C  prompt caching: many requests share the same long beginning')
# Invented prices for the exercise: 3 dollars per million input tokens, cached input tokens billed at a tenth of that.
PRICE, CACHED_PRICE = 3.00, 0.30
print(f'  {"scenario":<46}{"shared tokens":>14}{"new tokens":>12}{"cost, no cache":>16}{"cost, cached":>14}{"saving":>9}')
for name, shared, fresh, requests_ in [('support bot with a long system prompt', 4_000, 300, 100_000), ('questions about one 100,000-token manual', 100_000, 200, 2_000),
                                       ('short prompts, nothing shared', 0, 400, 100_000)]:
    plain = (shared + fresh) * requests_ / 1e6 * PRICE
    cached = (shared * CACHED_PRICE + fresh * PRICE) * requests_ / 1e6 + shared / 1e6 * PRICE     # pay full price once to fill the cache
    print(f'  {name:<46}{shared:>14,}{fresh:>12,}{plain:>15,.0f}${cached:>13,.0f}${1 - cached / plain if plain else 0:>9.0%}')
print('  The saving depends entirely on how much of each request is identical to the last one, and on putting the shared')
print('  part first: a cache can only reuse a prefix.')
