## Goal

Turn three abstract ideas into things you can run: a test for linearizability, clocks that respect cause and effect, and an election that stays safe while the network misbehaves.

All three labs are plain Python simulations. No Docker needed.

## Lab 1: checking linearizability

```bash
python lab1_linearizability.py
```

The checker takes a history of reads and writes, each with a start and end time, and searches for a way to place every operation at one instant within its interval so that each read returns the latest write before it.

**What you should observe**

- Part A: a history where reads see 0, then 1, then 1 is linearizable. A history where one read sees 1 and a later read sees 0 is not.
- Part B: reading from the leader, no history fails. Reading from an asynchronous follower, about one history in ten fails with a short lag, and most fail with a long lag.

**Try**

1. Write a history with two overlapping writes and one read that makes the checker return False. What is the smallest such history?
2. The checker is a brute-force search. Time it on histories of 8, 12 and 16 operations. What does that suggest about testing real systems?

## Lab 2: logical clocks

```bash
python lab2_logical_clocks.py
```

Three nodes with wall clocks off by 0, minus 40 and plus 25 ms exchange messages. Every event is stamped four ways.

**What you should observe**

- Part A: by wall clock, dozens of messages appear to arrive before they were sent. By Lamport timestamp and by hybrid clock, never.
- Part B: every event has a distinct (counter, node) pair, which gives one total order.
- Part C: vector clocks identify a share of event pairs as concurrent. Lamport timestamps order those pairs anyway.
- Part D: the hybrid clock stays within about 40 ms of true time, the size of the clock skew. The Lamport counter is just a count.

**Try**

1. Raise the skew to plus or minus 500 ms. Which results change and which do not?
2. Raise the chance of sending a message from 0.08 to 0.8. What happens to the share of concurrent pairs, and why?

## Lab 3: leader election

```bash
python lab3_leader_election.py
```

Five nodes. In two rounds out of three the network splits into two groups at random. Nodes that can talk share the highest term they know, a node without a leader may stand for election, and each node votes once per term.

**What you should observe**

- Thousands of elections succeed and thousands fail; the failures are candidates stuck in a minority.
- No term ever has more than one leader, and there is never a round in which two leaders could both commit a write. The script asserts both.
- There are well over a thousand rounds in which two nodes *believe* they are leader at once, and thousands of writes from out-of-date leaders are rejected.

That last pair is the lesson. You cannot stop a node from believing it is leader. You can stop it from getting anything decided.

**Try**

1. Change `MAJORITY` to 2. Which line of the output breaks first?
2. Remove the one-vote-per-term rule. What happens to "terms with more than one leader"?
3. Use 4 nodes instead of 5. How many failures can the cluster survive, compared with 3 nodes?

## Write up in NOTES.md

Record Part B from lab 1, Part A from lab 2, and the six counts from lab 3. Then answer: name something in a system you know that must have exactly one owner at a time. What enforces that today?
