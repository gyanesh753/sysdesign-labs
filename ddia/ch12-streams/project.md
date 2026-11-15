## Goal

Build the core of a log-based broker, see what the choice of clock does to a simple count, and keep derived data in step with a database the reliable way.

All three labs are plain Python. No Docker needed; lab 3 uses an in-memory SQLite database.

## Lab 1: a log-based broker

```bash
python lab1_log_broker.py
```

3,000 payment events are appended to a three-partition log. A consumer adds them up, committing its offset every 50 messages and crashing every 400.

**What you should observe**

- Part A: the consumer that simply adds every message it receives ends with a total a few thousand too high, because 44 messages were delivered twice. The consumer that records which offsets it has applied gets the exact total from the same deliveries.
- Part B: each partition holds only some of the users, and every event for a given user is in one partition.
- Part C: a second consumer reads the same log from the start and builds per-user totals.
- Part D: a changelog of 20,000 profile updates compacts to 50 records, one per user.

**Try**

1. Commit the offset after every message instead of every 50. Are there still duplicates? What does it cost in a real system?
2. In the idempotent consumer, imagine the total and the applied offset are saved in two separate steps and a crash falls between them. Which order of saving is worse?

## Lab 2: windows and time

```bash
python lab2_windows.py
```

The truth is 200 clicks a minute with a burst of 600 in minute 5. Four percent of events arrive late, and the processor is down during minutes 7 and 8.

**What you should observe**

- By processing time: minutes 7 and 8 show 0 and minute 9 shows about 600. None of that happened.
- By event time with a 5-second wait: the shape is right, each minute is a few short, and 79 late events are dropped.
- By event time with a 180-second wait: the counts are essentially exact, with 1 event dropped. The price is that every minute's count is reported three minutes later.

**Try**

1. Instead of dropping late events, add them to their window and count how many windows needed a correction after being published.
2. Change the windows to hopping windows of five minutes that advance every minute. How many windows does each event belong to?

## Lab 3: dual writes and change data capture

```bash
python lab3_cdc.py
```

**What you should observe**

- Part A: when two clients each write to the database and then the cache, the two systems end up with different values in a third of the races.
- Part B: every change to the `products` table is recorded by a trigger in a `changes` table. A follower that has read only part of it is behind but not wrong. After crashing and resuming from its saved position, its cache and search index match the database exactly; the script asserts this.

**Try**

1. Make the follower apply changes in a shuffled order. How quickly does the assertion fail?
2. Add a second follower that maintains the average price per word. Does anything about the database or the first follower need to change?

## Write up in NOTES.md

Record the two totals from lab 1, the table from lab 2, and the Part A percentage from lab 3. Then answer: find a place in a system you know where the same data is written to two stores. Which of the two failure modes could happen there?
