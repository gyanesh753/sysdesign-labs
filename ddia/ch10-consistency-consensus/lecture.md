## The strongest guarantee

Most replicated databases promise eventual consistency: stop writing, wait, and all replicas will agree. That says nothing about when, and chapter 6 showed how confusing the meantime can be.

This chapter goes to the other extreme. It asks what the strongest guarantee looks like, what it costs, and how it is built. The answer to the last question is consensus, which is the hardest and most useful tool in distributed computing.

## Linearizability

### What it means

The idea of **linearizability** is to make a replicated system behave as if there were only one copy of the data and every operation took effect at a single instant.

The practical test is recency. As soon as one client has completed a write, or has read a new value, every read that starts afterwards must return that value or a newer one. A value never appears to go backward. If a client is told a write succeeded, nobody can later read the old value.

During a write, reads that overlap with it may return either the old or the new value. But once any read has returned the new one, the switch has happened for everyone. Lab 1 contains a small checker for exactly this.

### Linearizability is not serializability

The two words are easy to confuse.

- **Serializability** is about transactions that touch several objects. It guarantees the result equals some one-at-a-time order, without saying which order.
- **Linearizability** is about reads and writes of a single object, and it concerns real time: the result must reflect the latest completed write.

A database can offer either without the other. Snapshot isolation, for instance, deliberately reads from an older snapshot, so it is not linearizable.

### Where you need it

- **Locks and leader election.** Everyone must agree who holds the lock. Two nodes that both believe they acquired it is split brain.
- **Uniqueness constraints.** Two people registering the same username at the same moment: exactly one must succeed.
- **Two channels racing each other.** A service saves a file to storage and then sends a message telling a worker to process it. If the storage is not linearizable, the message can arrive before the file is visible, and the worker finds nothing.

### Which replication methods provide it

A single leader can, if reads go to the leader and the node really is the leader, which is the hard part. Multi-leader replication cannot, since leaders accept conflicting writes independently. Leaderless quorums usually do not, because of clock-based conflict resolution and the edge cases from chapter 6. Consensus algorithms do, and that is their purpose.

### The cost

Suppose replicas are cut off from each other by a network fault. A replica that cannot reach the others has two choices. It can refuse requests until the link is restored, which keeps the system linearizable and makes it unavailable. Or it can keep answering from what it has, which keeps it available and gives up linearizability. This choice is what the CAP theorem describes, and it applies only while the network is actually broken.

There is a second cost that applies all the time. Linearizable operations are slow, because they have to wait for network round trips. Many systems give up linearizability for speed, not for fault tolerance.

## Logical clocks and ID generators

### Generating IDs

A counter on a single node gives every record a unique number that also reflects the order of events. It is also a single point of failure and a bottleneck. The common ways around that all give something up:

- Give each node a block of numbers in advance, or have each node count in steps.
- Generate random IDs, long enough that collisions are implausible.
- Combine a wall-clock timestamp with a node number and a sequence number.

All three produce unique IDs. None guarantees that a later event gets a higher ID than an earlier one on another node, and the timestamp version inherits every clock problem from chapter 9.

### Lamport timestamps

A **Lamport timestamp** orders events without any real clock. Each node keeps a counter and increases it for every event. Every message carries the sender's counter, and a node that receives a message moves its own counter beyond the largest value it has seen.

The result is a pair: counter and node ID. Compare counters first, and break ties by node ID. That gives a total order over all events with one important property: if one event could have caused another, it comes first. The reverse is not true. Two events that had nothing to do with each other still get placed in some order, and you cannot tell from the timestamps that the order is arbitrary. Version vectors can tell, at the cost of being much larger.

### Hybrid logical clocks

A Lamport counter bears no relation to the time of day. A **hybrid logical clock** combines the two ideas: it stays close to the wall clock, but like a Lamport clock it never goes backward and always moves past any timestamp it receives. You get timestamps that look like real times and still respect cause and effect.

### What they cannot decide

Logical timestamps tell you the order of events after the fact. They cannot tell you, right now, that you have seen everything. To grant a username you would need to know that no other node is at this moment handling a request with an earlier timestamp, and you cannot know that without hearing from every node. If one node is unreachable, you are stuck.

Deciding something on the spot, with a guarantee that the decision will not be contradicted, needs more than ordering. It needs consensus.

:::checkpoint[Two users request the same username on different nodes at the same moment. Each node stamps its request with a Lamport timestamp. Why is that not enough to decide the winner immediately?]
The timestamps do define a winner, but neither node can know it has the earliest request until it has heard from all the others. A node cannot answer its user on the spot, and if any node is unreachable it cannot answer at all.
:::

## Consensus

### The problem and why it is hard

**Consensus** means getting several nodes to agree on something. Stated as properties: all nodes decide the same value, the value was actually proposed by one of them, a decision once made is never changed, and every node that does not crash eventually decides.

It sounds simple and has a long history of subtly wrong solutions. There is even a proof that no algorithm can guarantee a decision in a network where delays are completely unbounded and a node may crash. Real systems get around that by using timeouts to suspect failures. That is enough to make consensus work in practice, as long as it never breaks agreement when a suspicion turns out to be wrong.

### Many faces of one problem

A striking fact about consensus is how many problems turn out to be the same problem in different clothes:

- A **compare-and-set** operation: set this value only if it is still what I expect.
- A **shared log**: every node appends entries and all nodes read them in the same order.
- A **lock or lease** that at most one node holds.
- A **uniqueness constraint**.
- **Atomic commit**: all participants commit or all abort.
- A counter that hands out the next number to exactly one caller.

Solve any one of these in a fault-tolerant way and you can build the others from it. This is why one well-tested consensus implementation can serve so many purposes.

### How it works in practice

The widely used algorithms, such as Raft and the Paxos family, share one shape. They maintain a shared log, and they use a leader.

Leadership is divided into numbered periods, called terms or epochs. To become leader for a new term, a node must collect votes from a majority, and each node votes once per term. So there is at most one leader per term. Before the leader can treat a log entry as decided, it must again get it accepted by a majority.

Two majorities always share at least one node. So if an old leader, unaware that it has been replaced, tries to get an entry accepted, at least one node it contacts knows about the newer term and refuses. The old leader may *believe* it is still in charge, which cannot be prevented, but it cannot get anything decided. Lab 3 shows both halves of that statement.

### What it costs

Consensus needs a majority to make progress: three nodes tolerate one failure, five tolerate two. A minority that is cut off stops accepting writes. Every decision takes network round trips to a majority. And on a network with highly variable delays, nodes may keep suspecting the leader and holding elections instead of doing useful work.

## Coordination services

Few teams should implement consensus themselves. It is normally used through a **coordination service** such as ZooKeeper or etcd: a small, linearizable key-value store replicated with a consensus algorithm. It holds little data, changes slowly, and the rest of the system relies on it for a handful of things:

- Locks and leases, with a number that increases on every change and can serve as a fencing token.
- Failure detection: a client's entries disappear when its session times out.
- Notifications when something changes, so that clients need not poll.
- Deciding which node is the leader, or which node owns which shard, and letting others look that up.

## What the labs show

- **Lab 1** checks histories of reads and writes for linearizability and finds the violations a lagging follower produces.
- **Lab 2** runs wall clocks, Lamport timestamps, vector clocks and a hybrid clock side by side on three nodes with skewed clocks.
- **Lab 3** holds thousands of elections over a network that keeps splitting, and checks that no term ever has two leaders.
