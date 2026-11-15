# lab2_clocks.py - DDIA Ch 9: clocks on different machines disagree, and ordering events by timestamp loses data
import numpy as np

rng = np.random.default_rng(9)

print('PART A  measuring a duration with a time-of-day clock that gets corrected halfway through')


class Machine:
    """A quartz clock that runs slightly fast and is periodically reset to the true time by a time server."""

    def __init__(self, drift_ppm):
        self.rate, self.offset_ms, self.elapsed_true = 1 + drift_ppm / 1e6, 0.0, 0.0

    def run(self, true_ms):
        self.elapsed_true += true_ms
        self.offset_ms += true_ms * (self.rate - 1)

    def time_of_day(self):
        return self.elapsed_true + self.offset_ms            # can jump when synchronized

    def monotonic(self):
        return self.elapsed_true * self.rate                 # never jumps; only good for measuring intervals

    def sync(self):
        self.offset_ms = 0.0                                 # step straight back to the true time


m = Machine(drift_ppm=200)                                   # 200 parts per million: about 17 seconds a day
m.run(3_600_000)                                             # an hour passes; the clock is now 720 ms fast
start_wall, start_mono = m.time_of_day(), m.monotonic()
m.sync()                                                     # the time server corrects it...
m.run(100)                                                   # ...and then a 100 ms operation finishes
print(f'  true duration 100 ms | time-of-day clock says {m.time_of_day() - start_wall:+.0f} ms | monotonic clock says {m.monotonic() - start_mono:+.1f} ms')

print('\nPART B  last write wins across two nodes whose clocks differ')
print('  A client writes to node 1, sees it succeed, then writes a newer value to node 2. Which one survives?')
print(f'  {"clock skew":>12}{"newer write discarded":>26}')
gaps = rng.exponential(20, 200_000)                          # ms between the first write and the second
for skew in [0, 1, 5, 20, 100]:
    # node 2's clock is behind node 1's by `skew` ms, so the later write gets the EARLIER timestamp when gap < skew
    print(f'  {skew:>9} ms{(gaps < skew).mean():>25.1%}')
print('  Nothing reports an error. The newer value simply disappears.')

print('\nPART C  honest clocks: a reading is a range [earliest, latest], not a point')
t = np.sort(rng.uniform(0, 60_000, 20_000))                  # 20,000 events in one minute
gap_to_next = np.diff(t)
print(f'  {"uncertainty":>13}{"neighbouring events whose order is certain":>46}')
for u in [0.1, 1, 7, 50]:
    # two events can be ordered for sure only if their ranges do not overlap, i.e. they are more than 2u apart
    print(f'  {"+/- " + str(u) + " ms":>13}{(gap_to_next > 2 * u).mean():>45.1%}')
