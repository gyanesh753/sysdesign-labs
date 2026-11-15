## Goal

Watch the three replication designs misbehave in controlled conditions, and see exactly what each remedy does and does not fix.

All three labs are plain Python simulations that run in a second or two. No Docker needed.

## Lab 1: replication lag

```bash
python lab1_replication_lag.py
```

One leader, three asynchronous followers, 200 users who mostly read their own profile and sometimes update it. The script counts two bad experiences under three read policies.

**What you should observe**

- Reading from any follower: about 7% of reads miss the user's own recent write, and a small fraction (well under 1%) show older data than the user saw before.
- Sticky follower: time never runs backward (0.00%), but the user's own write is still missing just as often. One replica is consistent with itself and can still be behind the leader.
- Own writes from the leader: the missing-write problem is gone (0.00%), at the cost of sending about 14% of reads to the leader.

Each remedy fixes exactly one anomaly. That is the lesson: these are separate guarantees, and you choose them one by one.

**Try**

1. Combine the two remedies. Do both columns reach zero?
2. Raise `MEAN_LAG` to 300. Which numbers change, and by how much?
3. The "recently wrote" window is five times the mean lag. What happens if it is shorter than the lag?

## Lab 2: quorums

```bash
python lab2_quorums.py
```

**What you should observe**

- Part A: every cell where w + r is greater than n shows 0% stale reads. Everywhere else the chance is real, up to 80% for w = 1, r = 1.
- Part B: with n = 5, w = 3, r = 3, the system keeps working with one or two nodes down and stops when three are down.
- Part C: two stale replicas are repaired within a handful of reads.

**Try**

1. For n = 5, list every (w, r) pair that guarantees fresh reads and still tolerates two nodes being down.
2. Make reads much more common than writes. Which pair would you pick, and what do you give up?

## Lab 3: concurrent writes

```bash
python lab3_concurrent_writes.py
```

Three replicas each accept clicks on a counter while out of touch with the others, then merge.

**What you should observe**

- Part A, last write wins: of 300 clicks, the merged counter reports about a third. The rest were acknowledged and then discarded.
- Part B, version vectors: the two edits made without knowledge of each other are reported as concurrent; the others are correctly ordered.
- Part C, the CRDT counter: after merging in five different orders, every result is 300.

**Try**

1. Add a decrement to the CRDT counter. Why does taking the maximum no longer work, and how would two counters fix it?
2. In Part B, write the version vector for an edit at replica 1 made after seeing the edit at replica 2 but not the merged one.

## Write up in NOTES.md

Record the table from lab 1, the Part A grid from lab 2, and the three results from lab 3. Then answer: for an application you use, which of the three replication designs do you think it uses, and what behaviour makes you think so?
