# lab1_timeouts.py - DDIA Ch 9: you cannot tell a slow node from a dead one. Every timeout is a bet.
import numpy as np

rng = np.random.default_rng(9)
N = 2_000_000
INTERVAL = 1_000                                   # a healthy node sends a heartbeat every 1,000 ms

# Delay of each heartbeat: usually a few ms, but the network queues and the sender sometimes pauses.
delay = rng.lognormal(np.log(5), 0.8, N)                               # ordinary network delay
congested = rng.random(N) < 0.01
delay[congested] += rng.lognormal(np.log(400), 1.0, congested.sum())   # 1%: congestion, retransmission
paused = rng.random(N) < 0.0005
delay[paused] += rng.uniform(1_000, 15_000, paused.sum())              # rare: the process stops for seconds (GC, VM migration)

p = np.percentile(delay, [50, 99, 99.9, 99.99])
print(f'heartbeat delay: p50={p[0]:.0f} ms   p99={p[1]:.0f} ms   p99.9={p[2]:.0f} ms   p99.99={p[3]:.0f} ms   max={delay.max():.0f} ms\n')
print('Declare the node dead if no heartbeat arrives within the timeout.')
print(f'{"timeout":>10}{"healthy node wrongly declared dead":>38}{"time to notice a real crash":>32}')
for timeout in [50, 200, 1_000, 5_000, 20_000]:
    false_alarms = (delay > timeout).mean()
    per_day = false_alarms * 86_400_000 / INTERVAL
    # a real crash is noticed, on average, half a heartbeat interval plus the timeout after it happens
    print(f'{timeout:>8} ms{per_day:>24,.1f} times per day{(INTERVAL / 2 + timeout) / 1000:>26.1f} s')
print('\nNo row is right. A short timeout causes false failovers; a long one leaves a dead node in charge.')
