# lab2_percentiles.py - DDIA Ch 2: percentiles, tail latency amplification, the averaging trap
import numpy as np
rng = np.random.default_rng(1)

# Part A: mean vs median vs tail
lat = np.concatenate([rng.lognormal(np.log(20), 0.4, 9_900),       # normal requests ~20 ms
                      rng.lognormal(np.log(800), 0.5, 100)])        # 1% slow outliers
print('PART A  mean=%.1f  p50=%.1f  p95=%.1f  p99=%.1f  p99.9=%.1f (ms)' %
      ((lat.mean(), *np.percentile(lat, [50, 95, 99, 99.9]))))

# Part B: tail latency amplification (a request waits for the slowest of k backend calls)
def backend(shape): return rng.lognormal(np.log(20), 0.7, shape)
single_p99 = np.percentile(backend(1_000_000), 99)
print('\nPART B  single-call p99 = %.1f ms' % single_p99)
print(' k   request p50   request p99   P(at least one call is slower than single p99)')
for k in [1, 5, 20, 50, 100]:
    req = backend((50_000, k)).max(axis=1)
    p50, p99 = np.percentile(req, [50, 99])
    print(f'{k:>3}   {p50:9.1f}     {p99:9.1f}      theory {1 - 0.99 ** k:5.3f}  measured {(req > single_p99).mean():5.3f}')

# Part C: averaging percentiles is meaningless; merge the raw data (or histograms) instead
a = rng.lognormal(np.log(30), 0.3, 100_000)      # busy, healthy server
b = rng.lognormal(np.log(300), 0.8, 1_000)       # tiny, struggling server
avg_of_p99 = (np.percentile(a, 99) + np.percentile(b, 99)) / 2
true_p99 = np.percentile(np.concatenate([a, b]), 99)
print('\nPART C  average of per-server p99 = %.0f ms,  true p99 of all requests = %.0f ms' % (avg_of_p99, true_p99))
