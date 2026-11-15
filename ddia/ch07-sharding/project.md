## Goal

Measure what the choice of sharding scheme costs when a cluster changes, when the workload is uneven, and when you query by something other than the key.

All three labs are plain Python and run in a few seconds. No Docker needed.

## Lab 1: adding a node

```bash
python lab1_rebalancing.py
```

100,000 keys on 10 nodes, then an eleventh node is added. The ideal is to move one eleventh of the keys, about 9.1%.

**What you should observe**

- Hash mod N moves about 91% of the keys.
- A fixed set of 1,024 shards moves about 9%, and so does consistent hashing.
- Consistent hashing with one point per node leaves the busiest node with more than twice its fair share. With 200 points per node the load is within about 10% of even.

**Try**

1. Go from 10 nodes to 20 with hash mod N. Does doubling move less than adding one?
2. With the fixed-shards scheme, start with 16 shards instead of 1,024. What goes wrong when you add the eleventh node?

## Lab 2: skew

```bash
python lab2_skew.py
```

**What you should observe**

- Part A: sharding by timestamp sends all of today's 72,000 writes to one shard. Hashing spreads them evenly, and so does a key range on sensor then timestamp.
- Part B: the six-hour query for one sensor needs 1 shard with a key range on sensor then timestamp, and all 8 shards with hashing.
- Part C: a key receiving 30% of writes makes one shard about three times busier than its fair share. Salting the key with 16 suffixes brings the busiest shard down to about 1.2 times, and a read of that key now has to fetch 16 keys.

**Try**

1. In Part C, try 4 suffixes and 64. Where does the benefit level off?
2. In Part A, the sensor-first key range is slightly uneven. Why, and how would a real system fix it?

## Lab 3: secondary indexes

```bash
python lab3_secondary_indexes.py
```

**What you should observe**

- Both indexes return the same set of red cars; the script asserts this.
- The local index asks all 8 shards per query and writes to 1 shard per insert. The global index asks 1 shard per query and writes to about 2.6 shards per insert.
- Waiting for all 8 shards more than doubles the median lookup time and raises the 99th percentile by about half.

**Try**

1. Raise `SHARDS` to 64. What happens to the local index's median and tail latency?
2. Add a third indexed field. How does the global index's write cost change?

## Write up in NOTES.md

Record the table from lab 1, the three Part A rows from lab 2, and the two tables from lab 3. Then answer: for a dataset you know, what would you choose as the shard key, and which query would that choice make expensive?
