## Putting the pieces together

The earlier chapters described tools: replication, sharding, transactions, logs, batch and stream processing. This one steps back and asks how to assemble them into a system that is reliable and can keep changing. It is more opinion than fact, and it is fine to disagree with parts of it. The opinion is this: treat an ordered record of what happened as the centre of the system, derive everything else from it, and check correctness from one end to the other instead of trusting each component in the middle.

## Integrating data by deriving it

No single piece of software is good at everything, so real systems combine several: a transactional database, a search index, a cache, a warehouse, a model. The same information lives in all of them in different shapes, and the main difficulty is keeping them in agreement.

### One log, many consumers

The dependable way to do it follows from chapters 1 and 12. Decide which system is the source of truth for each piece of data. Record every change to it in a log, in a fixed order. Have every other system derive its contents by reading that log.

The traditional alternative is a distributed transaction that updates all the systems together. The two approaches fail differently. A distributed transaction links the systems tightly: if one is slow or down, the whole write stalls or aborts. Derivation from a log is asynchronous: a slow or broken consumer falls behind without affecting anyone else, and catches up later. The price is that the derived systems are a little out of date, so a user may not immediately see their own change everywhere.

### Where a single order runs out

All of this assumes the changes can be put into one sequence, which is easy when a single leader handles them. It becomes hard as the system grows: when one node cannot keep up, when several regions each accept writes, when separate services each keep their own data, or when devices work offline. Then there is no single order, and events that depend on each other can arrive in the wrong sequence. Working out which events caused which, and resolving conflicts between those that did not know of each other, is still an area without tidy answers.

### Batch and stream are the same idea

Batch and stream processing both do the same thing: take input, apply a function, produce derived output. Batch does it over all the data so far. Stream does it continuously as new data arrives. Modern engines treat a batch as a stream that happens to end.

Keeping the original input and being able to process it again is what makes a system easy to change. You do not have to migrate a dataset in place and hope. You build the new view next to the old one from the same input, compare them, move readers across gradually, and delete the old one when you are satisfied. If the new one turns out to be wrong, the old one is still there. Lab 1 does this in miniature.

## Unbundling the database

### A database does many jobs

Look inside a database and you find the same pattern. A secondary index is derived from the table. A materialized view is derived from a query. A replica is derived from the leader's log. When you create a new index, the database scans a consistent snapshot of the table and then keeps the index current by following later changes, which is exactly how a new consumer of a change stream gets started.

So a database can be seen as a bundle: storage, indexes, caches and replication, all kept consistent for you by one product.

### Composing specialized systems

The alternative is to take the bundle apart and run the pieces separately: one system for storage, another for full-text search, another for analytics, with a log connecting them. There are two halves to this. Presenting one query interface over many stores unifies reads, and it is the easier half. Keeping all the stores in step as data changes unifies writes, and it is the harder and more valuable half. An ordered log with consumers that can safely re-apply changes is a sturdier way to do that than distributed transactions across different products.

This is not an argument against integrated databases. If one product does what you need, use it; a single system is simpler to run. Unbundling pays off when no single product covers the range of things you need.

### Application code as a derivation

When data changes, something has to react: recompute a total, refresh a cache, send a notification. A spreadsheet gets this right. Change one cell and every formula that depends on it updates by itself. Most databases do not behave that way for arbitrary application logic.

The dataflow approach treats application code as a function that turns one dataset into another. Code subscribes to changes in its inputs and produces changes to its outputs, and the platform takes care of order and fault tolerance. Services that react to streams of events, instead of calling each other and waiting, are loosely coupled in the same way.

### The write path and the read path

Every derived view marks a boundary. On one side is work done ahead of time whenever data changes: the write path. On the other is work done when someone asks: the read path. An index, a cache and a precomputed timeline all move that boundary toward doing more at write time, so that reads are cheap. Where to put the boundary is the design decision behind the home timeline example in chapter 2.

You can push the boundary a long way. If the server sends changes to the user's device as they happen, the screen is itself a derived view kept up to date by a stream, and it keeps working from its local copy when the network is gone.

## Aiming for correctness

### The end-to-end argument

Suppose a user presses "Pay" and the response is lost. The app retries. Did the payment happen once or twice?

It is tempting to think that reliable components settle the matter. The network layer discards duplicate packets. The database has transactions. A stream processor promises exactly-once processing. Yet each of those covers only its own hop. The network cannot know that a request arriving on a new connection repeats an earlier one, and a transaction that runs twice commits twice.

This is the **end-to-end argument**: some properties can only be guaranteed by the two ends of a conversation, because only they know what the operation means. For duplicates, the remedy is to have the client generate a unique identifier for each thing the user intends to do, carry it through every layer, and have the system that performs the action record the identifiers it has handled and ignore repeats. Lab 2 shows suppression at the network layer catching only half the duplicates and the request identifier catching all of them.

The general point is that features lower down are useful, since they make problems rarer, but they do not remove the need to think about correctness at the level of the whole application.

:::checkpoint[A team says: "Our message broker guarantees exactly-once delivery, so customers cannot be charged twice." What have they overlooked?]
The broker's guarantee covers the hop from producer to consumer. A duplicate can enter before that, for example when the user's app retries a request whose response was lost, and it will then be delivered exactly once, as a second charge. Only an identifier created at the user's end and checked where the charge is made closes the gap.
:::

### Enforcing constraints without distributed transactions

A rule such as "usernames are unique" or "an account cannot go below zero" needs a single point where conflicting requests meet and one of them wins. That is consensus, as in chapter 10.

A log gives you such a point cheaply. Send all requests that could conflict, for example all requests for the same username, to the same partition. One consumer handles them strictly in order, and the first valid request wins.

An operation that touches several partitions can be handled in stages. First record the request, with its unique identifier, as one message. A processor then derives from it the separate instructions for each partition, and each consumer applies its instruction once, using the identifier to ignore repeats. If any stage crashes, it resumes and re-emits the same instructions, which are recognized as duplicates. The effect is all-or-nothing without an atomic commit across partitions.

### Timeliness and integrity

"Consistency" mixes two different things.

- **Timeliness** means users see up-to-date state. A violation is temporary: wait and it resolves.
- **Integrity** means the data is not corrupt, contradictory or missing. A violation is permanent until someone finds it and repairs it.

Integrity matters far more. A balance that appears a few seconds late is an annoyance. A payment that vanished is a disaster. Systems built on logs and derivation preserve integrity well, since changes are applied in order and repeats are harmless, while being relaxed about timeliness.

Many business rules need not be enforced at the instant of writing in any case. Airlines sell more seats than exist, and shops occasionally sell something they have run out of. The business accepts a small rate of violations and handles them afterwards with an apology and compensation. If that is acceptable, you can process optimistically, check afterwards, and avoid most coordination.

### Trust, but verify

We assume that data written correctly stays correct. At large scale that assumption fails occasionally. Hardware corrupts bits. Software has bugs, including the database itself. Checksums at one layer do not cover what happens between layers.

So build in ways to check. If derived data is a deterministic function of a log, you can derive it again and compare. Checking that everything is still intact from the original input to the final output catches problems that no single component would notice. And a log can be made tamper-evident by having each entry include a hash of the one before it, so that any change to history shows up. Lab 3 builds one.

Systems that are regularly audited are easier to change with confidence, which brings us back to the point of all this: making systems that can evolve.

## What the labs show

- **Lab 1** derives three views from one event log, adds a fourth later, fixes a bug by replaying, and detects a corrupted view by deriving it again.
- **Lab 2** sends 10,000 transfers over a connection that loses replies, with duplicate suppression at three different levels.
- **Lab 3** builds a hash-chained log and tries five ways of tampering with it.
