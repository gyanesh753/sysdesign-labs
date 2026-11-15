## Input that never ends

A batch job has an input of known size, and it finishes. Most real data is not like that. Users keep clicking, sensors keep reporting, orders keep coming. A batch job copes by cutting the input into days or hours, which means its results are always at least a day or an hour old.

**Stream processing** drops the cutting. It handles each **event** shortly after it happens. An event is a small, self-contained, immutable record of something that occurred at a particular time. A producer creates it, and any number of consumers may process it. Related events are grouped into a named stream or topic.

## Getting events from producers to consumers

### Two questions to ask

Any system that carries messages can be understood by asking two things.

What happens when producers send faster than consumers can handle? There are only three options: drop messages, buffer them in a queue, or slow the producer down, which is called backpressure.

What happens when a node crashes or goes offline? Either messages may be lost, or the system pays for durability by writing to disk and replicating.

### Traditional message brokers

A message broker is a server that producers and consumers both connect to. It takes messages from producers, holds them, and hands them to consumers, who therefore need not be online at the same moment.

Two delivery patterns are used. With load balancing, each message goes to one of several consumers, which share the work. With fan-out, each message goes to every interested consumer.

To avoid losing work, the broker waits for a consumer to acknowledge each message. If the acknowledgment does not come, perhaps because the consumer crashed, the broker delivers the message again to someone else. Two consequences follow. A message can be processed more than once, and with load balancing, messages can be processed out of their original order. Once acknowledged, a message is deleted.

### Log-based brokers

A different design borrows from databases. The broker appends every message to a **log** on disk and never modifies it. A consumer reads the log in order, like reading a file.

To scale beyond one disk the log is split into partitions. A producer chooses the partition, usually by hashing a key, so all messages with the same key land in the same partition in the order they were sent. A consumer tracks its place in each partition with a single number, the **offset** of the next message to read. A group of consumers shares the work by taking different partitions.

The differences from a traditional broker are worth listing:

- Ordering is guaranteed within a partition, since one consumer reads it sequentially.
- A consumer that crashes resumes from its last recorded offset and processes again whatever came after it.
- Reading does not delete anything. A new consumer can start from the beginning and process the entire history, and a slow consumer does not get in the way of others.
- Disk is finite, so old segments are eventually discarded. A consumer that falls further behind than the retention period misses messages.

## Databases and streams

### Keeping systems in sync

Most applications keep the same data in several places: a database, a cache, a search index. The obvious way to keep them in step is for the application to write to each, known as **dual writes**. It fails in two ways. If two clients update the same item at nearly the same time, their writes can reach the two systems in different orders, leaving them permanently disagreeing. And if one write succeeds and the other fails, they disagree again. Nothing in the system notices either case.

### Change data capture

The fix is to have a single source of truth and let everything else follow it. A database already records every change, in order, in its replication log. **Change data capture** makes that log available as a stream. The search index and the cache become consumers that apply the changes in the same order the database committed them. They may lag, but they cannot end up with a different result.

A new consumer cannot always replay the log from the beginning of time, so it starts from a consistent snapshot of the database and continues from the log position the snapshot corresponds to. **Log compaction** offers another way: the broker keeps at least the most recent message for each key and discards older ones, so the log stays bounded while still containing the full current state.

Where an application must both update its database and publish an event, a common pattern is to write the event into a table in the same database transaction as the change, and have change data capture publish it from there.

### Events as the source of truth

Chapter 3 introduced event sourcing, which reaches the same place from the other direction. Change data capture extracts low-level changes from a database that the application treats as mutable. With event sourcing the application itself writes immutable events that describe what happened, and the current state is derived from them.

Either way, there is a useful way of seeing a database: the log of changes is the primary thing, and the tables you query are a cached summary of it. Keeping the log makes it possible to derive several different views from the same events, to add a new view later, and to investigate what went wrong after a bug. Keeping everything forever has limits, though: storage, and the duty to delete personal data on request.

## Processing streams

A stream processor reads one or more streams and writes others. The main uses are detecting patterns as they occur, such as fraud or a failing machine; computing running statistics over recent time; and keeping derived data such as search indexes and precomputed views up to date.

### Reasoning about time

"The number of requests in the last five minutes" hides a question: five minutes by whose clock?

- **Event time** is when the event actually happened, according to the device that recorded it.
- **Processing time** is when your stream processor got around to handling it.

The two can differ by seconds, or by hours if a phone was offline or your processor was down. If you count by processing time, a backlog being cleared after an outage looks like a sudden burst of activity that never took place. Lab 2 shows exactly that.

Counting by event time gives true answers but raises a new problem. You can never be sure that all events for a given minute have arrived. At some point you must declare the window complete and publish the count. An event that turns up later, a straggler, can either be dropped or cause a correction to be issued. How long to wait is a trade between completeness and delay.

A further wrinkle: event time comes from the user's device, whose clock may be wrong. Recording the device's own send time alongside the server's receive time lets you estimate how far off it is.

### Types of windows

- **Tumbling**: fixed length, no overlap. Every event belongs to exactly one window, such as each calendar minute.
- **Hopping**: fixed length, overlapping. A five-minute window that advances every minute.
- **Sliding**: all events that fall within some interval of each other.
- **Session**: no fixed length. Events from one user are grouped until there is a gap of inactivity.

### Joins on streams

Joining needs state, because the matching event may not have arrived yet. Joining two streams means remembering recent events from each and matching those that fall within a window, for example a search and the click that followed it. Joining a stream with a table means keeping a local copy of the table, updated from its change stream, and using it to enrich each event, for example adding the user's profile to each action.

Time matters here too. If a profile changes, should an event be joined with the profile as it was when the event occurred, or as it is now? If the order of events across streams is not fixed, running the same job twice can give different answers.

:::checkpoint[A stream processor was down for two hours. After it restarts, a dashboard of "orders per minute" shows zero for two hours and then an enormous spike. What is the dashboard measuring?]
Processing time. The orders were placed steadily, but they were all processed in the minutes after the restart. Counting by the time each order was actually placed would show a flat line.
:::

## Fault tolerance

A batch job that fails is simply run again. A stream job never finishes, so that is not an option. Instead, stream processors periodically save a **checkpoint** of their state together with their position in the input. After a crash they restore the last checkpoint and reprocess from that position. Some achieve the same thing by cutting the stream into very small batches.

Reprocessing means some events are handled twice. The goal, usually called **exactly-once**, is that the visible result is the same as if each event had been handled once. Two techniques get you there. One is to make committing the output and advancing the input position a single atomic step, so that either both happen or neither. The other is **idempotence**: arrange for applying an event twice to have the same effect as applying it once, for example by storing the offset of the last applied message together with the state and skipping anything at or before it.

## What the labs show

- **Lab 1** builds a partitioned log in memory and shows redelivery after a crash, the idempotent fix, replay from the start, and compaction.
- **Lab 2** counts clicks per minute by processing time and by event time through an outage, with two different waiting periods for stragglers.
- **Lab 3** shows dual writes diverging, then keeps a cache and a search index exactly in step with a database by following its change log.
