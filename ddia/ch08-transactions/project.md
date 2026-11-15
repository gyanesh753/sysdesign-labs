## Goal

Reproduce the race conditions from this chapter with exact, repeatable interleavings, then lose updates for real on a database with real threads.

All three labs are plain Python. Lab 2 uses SQLite files in a temporary folder. No Docker needed.

## Lab 1: three race conditions, three isolation levels

```bash
python lab1_isolation_anomalies.py
```

The script contains a small store that keeps every committed version of every value, and can behave as read committed, snapshot isolation or serializable. Each scenario runs the same interleaving of two transactions at each level.

**What you should observe**

- Read skew: under read committed the auditor adds up 1,100 from accounts that only ever held 1,000. The other two levels give 1,000.
- Lost update: under read committed the counter ends at 11 instead of 12. Under the other two, the second transaction is aborted, retried, and the result is 12.
- Write skew: under read committed and under snapshot isolation the combined balance ends at minus 80, even though each withdrawal checked the rule first. Only serializable aborts the second withdrawal; on retry its check refuses.

Read the `commit` method: the whole difference between the three levels is in about ten lines.

**Try**

1. Write a phantom scenario: two transactions each count the bookings for a room, find none, and insert one. Which levels allow two bookings? What does the store need to track to stop it?
2. In the serializable level, remove the condition `and self.writes`. Which scenario changes, and is the new behaviour wrong or merely stricter than necessary?

## Lab 2: a real database

```bash
python lab2_lost_update_sqlite.py
```

Four threads each increment one counter 150 times, so the correct final value is 600.

**What you should observe**

- Read then write with no protection: the final value is far short of 600. Most increments are lost.
- Atomic update, explicit lock, and compare-and-set all reach exactly 600.
- Compare-and-set needs a few hundred retries to get there. The explicit lock needs none but takes longer than the atomic update, because the threads queue.

**Try**

1. Remove the `time.sleep` from the unprotected version. Are updates still lost? What does that tell you about testing for race conditions?
2. Raise the thread count to 16. How do the retries and the time of each safe approach scale?

## Lab 3: two-phase commit

```bash
python lab3_two_phase_commit.py
```

**What you should observe**

- When everyone votes yes, all commit. When one votes no, all abort.
- If the coordinator crashes after the participants have prepared, both participants are stuck in the prepared state and another transaction that needs the same rows is blocked.
- After restart, the outcome depends only on the coordinator's log: commit if the decision was logged before the crash, abort if it was not.

**Try**

1. Let one prepared participant give up and abort on its own after a timeout, then recover the coordinator with a logged commit. What state is the system in?
2. Add a third participant that crashes after voting yes. What must it have saved to disk before voting for recovery to work?

## Write up in NOTES.md

Record the nine results from lab 1 and the table from lab 2. Then answer: find out which isolation level your main database uses by default, and name one operation in your application that it leaves exposed.
