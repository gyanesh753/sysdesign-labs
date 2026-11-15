# lab2_windows.py - DDIA Ch 12: counting clicks per minute when events arrive late and the processor falls behind
import numpy as np

rng = np.random.default_rng(12)
MINUTES = 12

# What really happened: 200 clicks a minute, with a burst of 600 in minute 5.
event_time = np.concatenate([m * 60 + rng.uniform(0, 60, 600 if m == 5 else 200) for m in range(MINUTES)])
# How long each event takes to reach us: usually under a second, but 4% come from phones that were offline.
delay = rng.exponential(0.5, event_time.size)
late = rng.random(event_time.size) < 0.04
delay[late] = rng.uniform(5, 150, late.sum())
arrival = event_time + delay
# The stream processor was down from 7:00 to 9:00 and worked through the backlog when it came back.
processed_at = np.where((arrival >= 420) & (arrival < 540), 540 + (arrival - 420) / 60, arrival)

order = np.argsort(processed_at)
event_time, processed_at = event_time[order], processed_at[order]
true = np.bincount((event_time // 60).astype(int), minlength=MINUTES)[:MINUTES]
by_processing = np.bincount((processed_at // 60).astype(int), minlength=MINUTES + 4)[:MINUTES]


def by_event_time(allowed_lateness):
    """Tumbling one-minute windows on EVENT time. A window is closed once the watermark passes its end.
    Watermark = the latest event time seen so far, minus the lateness we are willing to wait for."""
    counts, dropped, watermark = np.zeros(MINUTES, int), 0, 0.0
    for t in event_time:                                   # events in the order the processor handles them
        watermark = max(watermark, t - allowed_lateness)
        window = int(t // 60)
        if (window + 1) * 60 <= watermark:
            dropped += 1                                   # its window was already closed and reported
        else:
            counts[window] += 1
    return counts, dropped


short, dropped_short = by_event_time(5)
long_, dropped_long = by_event_time(180)
print('clicks per minute')
print(f'{"minute":>7}{"what happened":>15}{"by processing time":>21}{"by event time, wait 5s":>25}{"by event time, wait 180s":>27}')
for m in range(MINUTES):
    print(f'{m:>7}{true[m]:>15}{by_processing[m]:>21}{short[m]:>25}{long_[m]:>27}')
print(f'{"":>7}{"":>15}{"":>21}{f"{dropped_short} events dropped":>25}{f"{dropped_long} events dropped":>27}')
print('\nProcessing time reports the outage as two silent minutes followed by a spike that never happened.')
print('Event time gets the shape right. Waiting longer loses fewer stragglers, but every result is reported later.')
