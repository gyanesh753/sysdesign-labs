## Goal

Put numbers on three ideas from the chapter: where a feed design puts its work, why tails matter more than averages, and how retries can keep a system down.

All three labs are plain Python simulations. No Docker needed, and each runs in a few seconds.

## Lab 1: three timeline designs

```bash
python lab1_timelines.py
```

The script builds a follow graph of 10,000 users where a few accounts are followed by almost everyone, then replays 60,000 posts and 3,000 timeline reads against three designs: A merges at read time, B fans out at write time, C is the hybrid that treats heavily followed accounts separately.

**What you should observe**

- Writes: A is nearly free. B's typical write is small, but its p99 and maximum are far larger, because a post by a popular account is copied to thousands of timelines.
- Reads: B is by far the fastest. A is the slowest, by a factor of a hundred or more. C sits between them.
- C's p99 write is clearly lower than B's: the expensive posts were moved to the read path.

The printed "fan-out per post" line is worth a look: compare the mean with the p99 and the maximum. That gap is the skew the lecture talks about.

**Try**

1. Change `CELEB` from 1,000 to 100 and to 5,000. How do C's write tail and read time move, and where would you set it?
2. Change the skew exponent `0.9` to `0.5` (flatter) and `1.2` (more extreme). Which design is hurt most by skew?

## Lab 2: percentiles

```bash
python lab2_percentiles.py
```

**What you should observe**

- Part A: the mean is about 50% above the median, and p99.9 is in the seconds while the median is 20 ms. The mean describes nobody's experience.
- Part B: the "measured" column tracks `1 - 0.99^k` closely. With 100 backend calls, around 63% of requests are slower than a single call's p99.
- Part C: the average of the two servers' p99s is roughly ten times the true p99 of all requests combined.

**Try**

1. In Part B, make the request wait for only the fastest 95% of calls (drop the slowest 5% of each row). How much of the tail goes away? This is the idea behind giving up on stragglers.
2. In Part C, give server `b` the same number of requests as `a`. Is the average of p99s any closer to the truth?

## Lab 3: retry storm

```bash
python lab3_retry_storm.py
```

A server that can handle 100 requests per second receives 80. For five seconds (t=20 to t=25) its capacity drops to 35. Clients time out after one second and try up to four times. The script runs this under three policies and prints the queue length and total successful requests every five seconds.

**What you should observe**

- `naive` (retry immediately): the queue never drains. "goodput_total" stops rising at t=25 and stays flat to the end, long after capacity is back to 100. Every request the server finishes is one whose client already gave up.
- `backoff` (exponential backoff with jitter): in this model it ends up in the same state. Backoff spreads the retries out but does not reduce how many there are, and a queue that serves the oldest request first only ever does stale work.
- `shed` (reject when the queue is long, plus backoff): the queue stays short and goodput resumes within seconds of the slowdown ending.

So the system has two stable states at the same load, a healthy one and a broken one, and a five-second dip is enough to push it from one to the other. That is a metastable failure. In this simulation, bounding the queue is what gets it out; backoff alone does not.

**Try**

1. Keep the `backoff` policy but set `MAX_TRIES` to 1. Does it recover? What does that say about total retry volume versus retry timing?
2. Make the server drop requests whose deadline has already passed instead of working on them. Does `naive` recover now?
3. Find the largest `BASE` load at which `naive` still recovers on its own.

## Write up in NOTES.md

Record the p50 and p99 for each design in lab 1, the Part B table from lab 2, and the final queue length for each policy in lab 3. Then answer: for a service you know, what is its fan-out, and which client retry behaviour would worry you most?
