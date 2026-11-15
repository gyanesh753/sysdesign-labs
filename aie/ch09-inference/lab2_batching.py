# lab2_batching.py - AIE Ch 9: batching requests: more throughput, at the price of waiting
import numpy as np

rng = np.random.default_rng(9)
SLO_MS = 400                                   # a response slower than this counts as a failure for the user
SIM_SECONDS = 120


def batch_time_ms(size):
    return 60 + 12 * size                      # a batch of 8 takes 156 ms, not 8 x 72 ms: the hardware does the work in parallel


def simulate(rate, policy, max_batch=16, window_ms=30):
    """Requests arrive at random. One accelerator serves them. Returns per-request latency in ms."""
    arrivals = np.cumsum(rng.exponential(1000 / rate, int(rate * SIM_SECONDS)))
    latencies, i, clock = [], 0, 0.0
    while i < len(arrivals):
        clock = max(clock, arrivals[i])                         # wait for work if idle
        if policy == 'one at a time':
            j = i + 1
        elif policy == 'static batch of 16':
            j = min(i + max_batch, len(arrivals))
            clock = max(clock, arrivals[j - 1])                 # wait until the batch is full, however long that takes
        else:                                                   # dynamic: wait a short window, take whatever has arrived
            clock = max(clock, arrivals[i] + window_ms)
            j = i + 1
            while j < len(arrivals) and j - i < max_batch and arrivals[j] <= clock:
                j += 1
        clock += batch_time_ms(j - i)
        latencies += list(clock - arrivals[i:j])
        i = j
    return np.array(latencies)


print(f'one accelerator; a single request takes {batch_time_ms(1)} ms, a batch of 16 takes {batch_time_ms(16)} ms; users give up after {SLO_MS} ms\n')
print(f'{"load":>14}{"policy":>22}{"median":>10}{"p95":>10}{"within the limit":>18}{"goodput":>12}')
for rate in [5, 12, 40, 60]:
    for policy in ['one at a time', 'static batch of 16', 'dynamic batching']:
        lat = simulate(rate, policy)
        ok = (lat <= SLO_MS).mean()
        fmt = lambda v: f'{v:,.0f} ms' if v < 100_000 else 'minutes'
        print(f'{f"{rate} req/s":>14}{policy:>22}{fmt(np.median(lat)):>10}{fmt(np.percentile(lat, 95)):>10}{ok:>18.0%}{rate * ok:>9.1f}/s')
    print()
print('One at a time is fastest when traffic is light and collapses once requests arrive faster than it can serve them.')
print('A fixed batch size is the reverse: at light load everyone waits for the batch to fill.')
print('Waiting a short window and taking whatever has arrived works across the range. Goodput counts only requests served in time.')
