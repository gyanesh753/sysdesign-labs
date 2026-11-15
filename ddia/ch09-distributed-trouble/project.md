## Goal

Put numbers on three things that are easy to believe in theory and easy to forget in practice: timeouts are guesses, clocks disagree, and a process can stop at any line.

All three labs are plain Python simulations. No Docker needed.

## Lab 1: timeouts

```bash
python lab1_timeouts.py
```

The script draws two million heartbeat delays. Most are a few milliseconds; 1% are hit by congestion and a few in ten thousand by a pause of several seconds.

**What you should observe**

- The median delay is 5 ms, but the 99.9th percentile is around 2 seconds and the worst case is tens of seconds.
- A 50 ms timeout wrongly declares a healthy node dead about a thousand times a day. A 5-second timeout still does so a few dozen times a day. A 20-second timeout almost never does, but takes over 20 seconds to notice a real crash.

**Try**

1. Require three consecutive missed heartbeats before declaring a node dead. What happens to both columns?
2. Double the rate of long pauses. Which timeouts are affected most?

## Lab 2: clocks

```bash
python lab2_clocks.py
```

**What you should observe**

- Part A: an operation that truly took 100 ms is measured as minus 620 ms by the time-of-day clock, because the clock was corrected by 720 ms in the middle. The monotonic clock says 100 ms.
- Part B: with clocks only 5 ms apart, last write wins discards about a fifth of the newer writes. At 20 ms it discards most of them.
- Part C: with an uncertainty of plus or minus 1 ms, only about half of neighbouring events can be ordered with certainty. At 7 ms almost none can.

**Try**

1. In Part B, change the average gap between writes from 20 ms to 500 ms. How does the loss rate change, and what does that say about when clock skew matters?
2. In Part A, reduce the drift to 20 parts per million and sync every 10 minutes. How large is the worst jump now?

## Lab 3: leases and fencing

```bash
python lab3_fencing.py
```

Client 1 takes a 10-second lease, checks that it is valid, and is then paused. Client 2 takes over the expired lease and writes. Client 1 wakes up and writes too.

**What you should observe**

- Without token checks, the final content is client 1's stale data: the newer write was overwritten.
- With token checks, client 1's write is rejected because its token is lower than one the storage has already seen.
- Over a million lease holders with mostly tiny pauses, stale overwrites happen about two hundred times without fencing and never with it.

**Try**

1. Make client 1 check the lease again immediately before writing. Does the count without fencing reach zero? Why not?
2. What goes wrong if two lock services hand out tokens independently?

## Write up in NOTES.md

Record the table from lab 1, the Part B table from lab 2, and both counts from lab 3. Then answer: find one timeout in a system you work on. How was its value chosen, and what happens on a false alarm?
