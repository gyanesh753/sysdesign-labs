## Why split the data

Replication puts the same data on several machines. **Sharding**, also called partitioning, does the opposite: it splits the data so that each record lives in exactly one shard, and puts different shards on different machines. The two are normally combined, so that each shard is itself replicated.

The reason to shard is scale. When the data or the write load is too much for one machine, sharding lets you spread it across many. A query that touches one shard runs on one machine, and adding machines adds capacity.

The cost is real, which is why the advice from chapter 1 applies: do not shard until you need to. You have to choose a key that decides where each record goes, and that choice is hard to change later. Anything that spans shards, such as a join, a secondary index or a transaction, becomes slower and more complicated. A single machine handles more than people expect.

### One shard per customer

Sharding is not only about size. A business serving many customer organizations can give each tenant its own shard or even its own database. That isolates tenants from each other's load and bugs, makes it simple to back up, restore, move or delete one customer's data, and lets a schema change be rolled out a few tenants at a time. It works less well when one tenant outgrows a machine, or when there are huge numbers of tiny tenants.

## Sharding by key range

The simplest scheme assigns each shard a continuous range of keys, like the volumes of a printed encyclopedia: A to C in one, D to F in the next. Within a shard the keys are kept sorted.

The strength is range queries. Everything between two keys sits together, so "all readings from this sensor for last week" is one scan on one shard. The boundaries need not be evenly spaced; they follow the data, and a shard that grows too large is split in two.

The weakness is that some key choices funnel all the activity to one place. If the key is a timestamp, every write happening now goes to the shard for today while the others sit idle. The usual fix is to put something else first in the key, such as the sensor ID, so that writes spread across sensors while each sensor's readings stay in time order.

## Sharding by hash of key

If you do not need range queries on the key, you can run it through a hash function first. A good hash turns even very similar keys into evenly scattered numbers, so the load spreads out. What you lose is ordering: neighbouring keys end up on unrelated shards.

The question is then how to turn a hash value into a node.

### Why not hash mod N

The obvious answer is to take the hash modulo the number of nodes. It spreads keys evenly and it is a trap. When the number of nodes changes, the result changes for almost every key. Lab 1 shows that going from 10 nodes to 11 moves about 91% of the data, when ideally only the one-eleventh destined for the new node would move.

### A fixed number of shards

A better approach separates two questions. First, which shard does a key belong to? Create many more shards than nodes, say a thousand, and assign each key to a shard permanently. Second, which node holds a shard? That is a small table which can change.

Adding a node now means moving a few whole shards to it. No key ever changes shard, and only the data that needs to move does. The number of shards is fixed up front, so it has to suit both the cluster you have and the one you expect to grow into.

### Hash ranges and consistent hashing

Another approach gives each shard a range of hash values and splits a shard when it grows too large, exactly as with key ranges but over hashes. **Consistent hashing** is a family of algorithms in the same spirit, designed so that when a node is added or removed, only a small share of keys are reassigned. One common form places each node at many points on a ring of hash values, and a key belongs to the next point around the ring. Using many points per node is what keeps the load even.

:::checkpoint[A cluster uses hash mod N and has 10 nodes. During a traffic peak someone adds an eleventh node to help. What happens?]
Nearly all the data starts moving between nodes at once, at the moment the cluster can least afford the extra load. A scheme that moves only the new node's share would have made the same change cheap.
:::

## Skew and hot keys

Hashing spreads keys evenly. It cannot spread a single key. If one key receives a large share of the traffic, as with a celebrity account or a product on sale, the shard holding it is overloaded however good the hash function is. Uneven load is called skew, and the busy shard is a hot spot.

There is no automatic cure. One technique is to add a random suffix to the hot key when writing, so its writes are spread over several keys on different shards. Reads then have to fetch all of those keys and combine them, and you need to track which keys are being treated this way. It is worth doing for a handful of known hot keys, not for everything.

## Rebalancing

As data and nodes change, shards have to move. The requirements are that load ends up fairly shared, that the database keeps serving reads and writes while data moves, and that no more data moves than necessary.

Whether this should be fully automatic is a judgement call. Automation is convenient, but moving data is expensive, and combined with automatic failure detection it can go wrong: an overloaded node is slow to respond, is judged dead, and the system reacts by moving load onto other nodes that are also struggling. Many teams keep a human in the loop to approve the plan.

## Request routing

A client needs to reach the node holding its key. Three arrangements are common: the client contacts any node, which forwards the request if needed; a routing tier in front of the cluster does the forwarding; or the client itself knows the assignment and connects directly.

In every case the hard part is keeping everyone's view of the assignment correct while it changes. Many systems keep the authoritative mapping in a separate coordination service that nodes and routers subscribe to. Others have the nodes spread the information among themselves by gossip.

## Secondary indexes

Sharding by key works well when you look records up by that key. A secondary index, such as "all cars that are red", does not map neatly to shards. There are two designs.

A **local** index means each shard indexes only its own records. Writing is simple, since a record and its index entries are in the same shard. Reading is expensive: a query on the indexed field has to be sent to every shard and the results combined, and it is only as fast as the slowest shard.

A **global** index covers all records and is itself sharded, by the indexed value. A query for red cars goes to the one index shard that holds "red". Writing is now the hard part: one record's index entries live on other shards, so a write touches several shards, and unless you use a distributed transaction the index is updated a little after the record.

| | Local index | Global index |
|---|---|---|
| Query on the indexed field | Ask every shard | Ask one index shard |
| Write | One shard | Several shards |
| Index up to date? | Yes, immediately | Often slightly behind |

:::spoken
A local index makes writes cheap and queries expensive, because every shard must be asked. A global index makes queries cheap and writes expensive, and it is often slightly behind the data.
:::

## What the labs show

- **Lab 1** adds one node to a cluster of ten under four schemes and counts how many keys move.
- **Lab 2** shows a timestamp key creating a hot shard, a range query scattering under hashing, and a hot key being salted.
- **Lab 3** builds both kinds of secondary index and compares what a query and a write cost.
