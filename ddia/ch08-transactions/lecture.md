## What a transaction gives you

A great deal can go wrong while an application is talking to a database. The database can crash halfway through a series of writes. The application can crash. The network can drop. Two clients can change the same data at the same moment.

A **transaction** is a way to stop worrying about most of that. The application groups several reads and writes into one unit. Either the whole unit takes effect, which is a commit, or none of it does, which is an abort. If it aborts, the application can simply try again, without having to work out which parts happened.

Transactions are not a law of nature. They were invented to make application code simpler, they cost performance, and different databases mean quite different things by the word. This chapter is about what exactly is being promised.

## ACID, one letter at a time

The guarantees are summarized as ACID. The acronym is used loosely, so it is worth being precise.

- **Atomicity** is about faults, not concurrency. If a transaction fails partway, everything it wrote is undone. A better name would be abortability.
- **Consistency** means your data obeys the rules of your application, such as debits equalling credits. The database can check a few rules for you, but keeping the data valid is the application's responsibility. This letter is the odd one out.
- **Isolation** is about concurrency. Transactions running at the same time should not interfere with each other. In the strict sense, the result should be the same as if they had run one after another.
- **Durability** means that once a transaction has committed, its data will not be lost in a crash. It is never absolute: disks fail, and so do whole datacentres.

Atomicity and isolation matter most when one transaction touches several records. A money transfer changes two balances. A row and its index entry must change together. Without multi-object transactions, every such case needs custom error handling in the application.

## Weak isolation levels

Full isolation is expensive, so databases offer weaker levels that prevent some race conditions and not others. Many applications run on a weak level without knowing which problems they are exposed to.

### Read committed

The most basic level makes two promises. No **dirty reads**: you only see data that has been committed, never another transaction's unfinished work. No **dirty writes**: you only overwrite data that has been committed.

This is the default in many databases. It prevents the most obviously wrong behaviour and little else.

### Snapshot isolation

Under read committed, a transaction that runs for a while can see the database change underneath it. Suppose an auditor adds up two accounts, and a transfer between them commits in between the two reads. The auditor sees the first account before the transfer and the second one after, and the total is wrong. This is called **read skew**. It is temporary, but a backup or a long report taken in that state would be inconsistent for good.

**Snapshot isolation** fixes it. Each transaction reads from a consistent snapshot of the database as of the moment it started. The database achieves this by keeping several versions of each row and showing each transaction only the versions that had committed before it began, a technique called multiversion concurrency control. A useful consequence: readers never block writers, and writers never block readers.

Be careful with names. Different databases call snapshot isolation "repeatable read" or even "serializable". Check what your database actually does.

### Lost updates

Two transactions each read a value, change it, and write it back. The second write is based on what it read earlier, so it overwrites the first, and one change disappears. A counter incremented twice goes up by one.

There are several remedies, and which is available depends on the database:

- **Atomic operations.** Ask the database to do the read and the write as one step, such as "set value to value plus one".
- **Explicit locking.** Lock the rows you are about to change when you read them, so that nobody else can read them for update in between.
- **Automatic detection.** Some databases notice a lost update under snapshot isolation and abort the later transaction so that it can retry.
- **Compare-and-set.** Write only if the value is still what you read; otherwise read again and retry.

### Write skew and phantoms

The subtlest problem is **write skew**. Two transactions read the same set of rows, each makes a decision based on what it saw, and each then writes to a *different* row. Neither overwrites the other, so nothing looks like a conflict, yet together they break a rule that each of them checked.

Lab 1 uses two linked bank accounts holding 60 each, with the rule that the combined balance must not go negative. Two withdrawals of 100, one from each account, both check the combined balance, both see 120, and both go ahead. The result is minus 80.

Snapshot isolation does not prevent this, because each transaction's snapshot was consistent. The pattern is always the same: a query checks some condition, the application decides, and a write changes the answer to that query. When the write is an insert that would have matched the query, such as a new booking for a room the query found free, the effect is called a **phantom**. There may be no existing row to lock at all.

| Race condition | Read committed | Snapshot isolation | Serializable |
|---|---|---|---|
| Dirty read, dirty write | Prevented | Prevented | Prevented |
| Read skew | Possible | Prevented | Prevented |
| Lost update | Possible | Depends on the database | Prevented |
| Write skew, phantoms | Possible | Possible | Prevented |

:::spoken
To summarize the table: read committed prevents only dirty reads and dirty writes. Snapshot isolation also prevents read skew, and in some databases lost updates. Only serializable isolation prevents write skew and phantoms.
:::

:::checkpoint[A booking system checks that a room is free, then inserts a booking. Two users book the same room at the same instant under snapshot isolation. Why are both bookings accepted?]
Each transaction's check ran against a snapshot in which the room was free, and each inserted a new row, so neither modified anything the other had written. This is write skew caused by a phantom. Only serializable isolation, or a constraint the database enforces itself, prevents it.
:::

## Serializability

**Serializable** isolation is the strongest level: the outcome is guaranteed to be the same as if the transactions had run one at a time, in some order. It prevents every race condition above. There are three ways to provide it.

### Actual serial execution

The simplest is to really run one transaction at a time, on a single thread. This became practical when memory grew cheap enough to hold a whole dataset and people noticed that most transactions are short. It needs each transaction submitted to the database as one piece of code, a stored procedure, so that the single thread never waits for the application. Throughput is limited to one CPU core, and transactions that span shards are much slower.

### Two-phase locking

For decades the standard approach was locking. A transaction takes a shared lock to read and an exclusive lock to write, and keeps its locks until it commits. Unlike snapshot isolation, readers block writers and writers block readers. To stop phantoms, the locks have to cover ranges of an index, not only existing rows. It is correct, but concurrency is poor, response times become unpredictable, and transactions can deadlock, in which case the database aborts one of them.

### Serializable snapshot isolation

The newest approach is optimistic. Transactions run on snapshots without blocking each other. The database tracks what each one read, and at commit time checks whether anything it read has since been changed by another transaction. If so, its decision may rest on a stale premise, and it is aborted and retried. This works well when conflicts are rare and transactions are short. Under heavy contention many transactions abort and the work is wasted.

## Distributed transactions

Everything so far assumed one database node. When a transaction writes to several nodes, atomicity becomes a problem in its own right: it must not commit on some nodes and abort on others.

### Two-phase commit

The classic solution adds a **coordinator**. In the first phase it asks every participant to prepare. A participant that answers yes is making a promise: it has stored everything it needs and will commit if told to, whatever happens. In the second phase, if every participant said yes, the coordinator writes the decision to its own log, which is the point of no return, and then tells everyone to commit. If anyone said no, it tells everyone to abort.

### In doubt

The weakness is the gap between the phases. A participant that has voted yes cannot decide on its own, since it does not know how the others voted. If the coordinator crashes at that point, the participant is **in doubt**: it must wait, holding its locks, until the coordinator recovers. Other transactions that need those rows are blocked for as long as that takes.

This is tolerable inside a single distributed database, where the coordinator's state can itself be replicated. It is much more troublesome across different systems, for example a database and a message broker tied together by a standard such as XA, where the coordinator is often a library inside one application server.

For the common case of processing a message exactly once, there is a simpler route than a distributed transaction: store the ID of each processed message in the database, in the same local transaction as the changes it caused. A redelivered message is then recognized and skipped.

## What the labs show

- **Lab 1** runs read skew, a lost update and write skew against a small multi-version store at three isolation levels.
- **Lab 2** loses updates on a real SQLite database with four threads, then fixes it three ways.
- **Lab 3** steps through two-phase commit, including a coordinator crash at each of the two critical moments.
