## Why keep copies

Replication means keeping the same data on several machines. There are three reasons to do it: the system keeps working when a machine fails, users can be served from a copy near them, and reads can be spread over more machines.

If the data never changed, this would be trivial: copy it once. Everything hard about replication comes from handling changes. There are three broad approaches, named after how many nodes accept writes: one leader, several leaders, or no leader at all.

## Single-leader replication

One replica is the **leader**. All writes go to it. It applies each write locally and sends the change to the other replicas, the **followers**, which apply the changes in the same order. Reads can go to the leader or to any follower.

### Synchronous or asynchronous

When the leader has written a change, should it wait for followers to confirm before telling the client "done"?

- **Synchronous**: it waits. The follower is guaranteed to have the data, but if that follower is slow or unreachable, writes stall.
- **Asynchronous**: it does not wait. Writes stay fast and the leader keeps working whatever the followers are doing, but a write the client was told succeeded can be lost if the leader fails before sending it on.

Making every follower synchronous would let any single outage stop all writes, so in practice at most one or two are, and fully asynchronous setups are very common.

### Adding followers and surviving failures

A new follower starts from a consistent snapshot of the leader, taken without stopping writes, and then asks for every change since the snapshot's position in the replication log. A follower that crashed recovers the same way: it knows the last change it applied and asks for everything after it.

A leader failure is harder. **Failover** means choosing a follower to promote, pointing clients at it, and making the rest follow it. Plenty can go wrong:

- With asynchronous replication, the new leader may be missing the old leader's last writes. If the old leader comes back, those writes conflict, and they are usually thrown away.
- Two nodes may both believe they are the leader, a situation called split brain. Both accept writes and the data diverges.
- The timeout that declares a leader dead is a guess. Too long means slow recovery. Too short means needless failovers, often during a load spike when they do the most harm.

### What travels in the log

The leader could send the SQL statements themselves, but anything nondeterministic, such as a call for the current time, gives different results on each replica. It could ship its low-level storage log, but that ties every replica to the same storage format and version. The usual choice is a **logical log**: a description of which rows were inserted, updated or deleted. It is independent of the storage engine, so replicas can run different versions, and other systems can consume it too.

## Replication lag

With asynchronous followers, a read from a follower may return slightly old data. If writes stopped, the followers would catch up, which is called **eventual consistency**. Normally the lag is a fraction of a second, but under load or network trouble it can stretch to minutes, and then three anomalies become visible.

### Reading your own writes

A user saves a change and reloads the page. The reload is served by a follower that has not received the write yet, and the change appears to be lost. The guarantee that prevents this is **read-your-writes** consistency. One way to provide it: read anything the user may have modified from the leader, or do so for a short time after the user's last write.

### Monotonic reads

A user reloads twice. The first read hits an up-to-date follower and the second a lagging one, so something they just saw disappears. Time seems to run backward. **Monotonic reads** guarantees you never see older data than you have already seen. A simple way to provide it is to always send a given user to the same replica.

A third guarantee, consistent prefix reads, says you see writes in an order that makes sense: never the answer before the question.

:::checkpoint[A user posts a comment, and their friend immediately says they cannot see it. Is that a violation of read-your-writes?]
No. Read-your-writes is a promise about a user's own writes. The friend seeing it a moment later is ordinary replication lag, which the guarantee does not cover.
:::

## Multi-leader replication

With one leader, every write must reach that one node. Allowing more than one node to accept writes helps in two situations.

One is running in several geographic regions: each region has its own leader, so users write to a nearby one, and a region can keep working if it is cut off from the others. The other is software that must work offline. A calendar app on your phone accepts changes with no network and syncs later. Every device is in effect a leader, and the lag between them can be days. Applications built this way are often called local-first, and the component that reconciles devices is a sync engine.

The price in both cases is the same: two leaders can change the same data at the same time, and neither finds out until later.

### Handling write conflicts

- **Avoid them.** Route all writes for a given record through the same leader. Simple and common, until that leader changes.
- **Last write wins.** Give each write a timestamp and keep the one with the highest. Every replica ends up agreeing, which is its appeal, but the other writes are silently discarded, and timestamps from different machines are not trustworthy.
- **Keep both and let someone merge.** Store the conflicting versions and have the application or the user resolve them.
- **Merge automatically.** Data types designed so that concurrent changes can always be combined, known as **CRDTs**, give every replica the same result regardless of the order in which changes arrive. Collaborative editors use these or a related technique called operational transformation.

## Leaderless replication

A third design has no leader. The client, or a coordinator acting for it, sends each write to all replicas and each read to several.

If a replica is down, the write goes ahead on the others. When that replica returns it has stale data, so reads ask several replicas and use version information to pick the newest answer. With **n** replicas, a write must be confirmed by **w** of them and a read must hear from **r**. If

```text
w + r > n
```

:::spoken
If w plus r is greater than n,
:::

then the set of nodes that took the write and the set consulted by the read must share at least one node, so the read sees the latest value. A typical choice is n of 3 with w and r of 2, which tolerates one node being down.

Stale replicas are repaired in two ways. **Read repair**: when a read notices a replica with an old value, it writes the newer one back. **Anti-entropy**: a background process compares replicas and copies missing data, which matters for values that are rarely read.

Quorums are weaker than they look. Two concurrent writes still need resolving, a write that reached fewer than w nodes is not rolled back, and a read that overlaps a write in progress may or may not see it. Treat quorum reads as very likely fresh, not as a guarantee.

## Detecting concurrent writes

Whether one write should overwrite another depends on what each writer knew. Write B **happens after** write A if B's author had seen A. If neither knew about the other, they are **concurrent**, no matter what the clocks say, and overwriting either one loses data.

To tell the difference, each replica keeps a counter that it increases on every write it accepts, and every value carries the set of counters its writer had seen. That set is a **version vector**. Comparing two version vectors tells you whether one value supersedes the other or whether they are concurrent, in which case both are kept as siblings to be merged.

## What the labs show

- **Lab 1** simulates asynchronous followers and counts how often users miss their own writes or see time go backward, under three read policies.
- **Lab 2** measures stale reads for every combination of w and r, and shows read repair.
- **Lab 3** counts clicks on three replicas with last write wins, with version vectors, and with a CRDT counter.
