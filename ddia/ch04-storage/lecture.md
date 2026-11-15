## Why look inside the engine

A database does two things: it stores what you give it and finds it again when you ask. You will rarely write a storage engine, but you will choose one and tune it, and you cannot do either well without a rough picture of what happens on disk. This chapter covers the two main designs for transactional workloads, then the very different design used for analytics, and finally indexes for text and for meaning.

One trade-off sits under everything here. An **index** is extra structure kept alongside the data so that reads do not have to scan everything. Every index speeds up some reads and slows down every write, because the index must be updated too. That is why databases do not index everything by default.

## Log-structured storage

### The simplest database

The fastest way to store a write is to append it to the end of a file. Appending is sequential, which disks of every kind handle well. The catch is reading: to find a key you must scan the file, and old values for the same key pile up.

Log-structured engines keep the cheap append and fix the rest with two ideas: keep the data sorted, and merge files in the background.

### SSTables and the LSM-tree

Writes go first into a sorted in-memory structure called the **memtable**. When it grows past a threshold it is written to disk as an **SSTable**: an immutable file of key-value pairs sorted by key. A new memtable takes over.

Sorted files have two useful properties. You can find a key with a sparse index and a short scan, and you can merge several files the way merge sort does, in one sequential pass. To survive a crash before the memtable is flushed, every write is also appended to a log on disk.

A read checks the memtable first, then the SSTables from newest to oldest, and returns the first match. A delete is recorded as a special marker called a tombstone, which hides older values until they are merged away. The whole arrangement is a log-structured merge-tree, or **LSM-tree**.

### Bloom filters

Looking for a key that does not exist is the worst case, because every SSTable has to be checked. A **Bloom filter** is a small bitmap kept per file that answers one question: is this key definitely absent, or possibly present? It never says "absent" wrongly, so the engine can skip most files without touching the disk.

### Compaction

Over time there are many SSTables containing overwritten values. **Compaction** merges them in the background, keeps only the latest value for each key, and drops tombstones. Two strategies are common. Size-tiered compaction merges files of similar size into larger ones, which favours write throughput. Leveled compaction keeps files in levels with non-overlapping key ranges, which favours reads and wastes less space, at the cost of rewriting data more often.

:::checkpoint[An LSM-based database slows down badly under a heavy write load, and the number of files keeps growing. What is happening?]
Compaction is not keeping up with incoming writes. More unmerged files means every read has more places to look, and disk usage grows. The engine has to throttle writes or be given more resources for compaction.
:::

## B-trees

The other family is older and still the default in most relational databases. A **B-tree** divides the data into fixed-size pages, typically a few kilobytes each. Each page holds sorted keys and pointers to child pages covering the ranges between those keys. A lookup starts at the root and follows pointers down to a leaf. Because each page points to hundreds of children, a tree only three or four levels deep covers an enormous number of keys.

Unlike an LSM-tree, a B-tree changes pages **in place**. An update rewrites the page that holds the key. An insert into a full page splits it in two and updates the parent. A crash halfway through such a change would leave the tree corrupt, so every change is first appended to a **write-ahead log**, which is replayed after a crash.

## Comparing the two

| | LSM-tree | B-tree |
|---|---|---|
| Writes | Sequential appends and merges; high throughput | Random page rewrites, plus the log |
| Reads | May check several files; Bloom filters help | One path from root to leaf; predictable |
| Disk space | Compact after merging, bloated before | Some space left empty inside pages |
| Background work | Compaction can interfere with requests | Little |

:::spoken
In short: an LSM-tree makes writes cheap and pays for it with background merging and reads that may check several files. A B-tree keeps each key in exactly one place, so reads are predictable, but each write rewrites a page at a random location.
:::

Both rewrite data more than once over its lifetime, an effect called write amplification. Sequential writing still matters on solid-state drives, which have their own internal garbage collection that random writes aggravate. As a rough guide, LSM-trees suit write-heavy workloads and B-trees suit read-heavy ones, but you have to test with your own workload to know.

Two further points. A table usually needs **secondary indexes** on columns other than the key, and they can be built on either structure. And some databases keep everything in memory, which is faster mostly because they avoid the overhead of encoding data for disk, not simply because disk is slow.

## Storage for analytics

### Column-oriented storage

An analytical query reads a few columns of a very large number of rows. A row-oriented engine would load every column of every row to answer it. A **column-oriented** engine stores all the values of one column together, with every column keeping its rows in the same order so that the nth value of each belongs to the same row. The query then reads only the columns it mentions.

### Compression and sort order

A column holds values of one type, often with few distinct values, and that compresses very well. Dictionary encoding replaces values with small numbers. Bitmaps and run-length encoding store "this value, repeated this many times". If the rows are sorted, the first sort column collapses into a handful of long runs. Lab 2 shows a column of half a million values shrinking to six runs.

Sorting makes single-row writes impractical, so column stores take writes in batches: new rows accumulate in memory and are periodically written as new sorted files, much like an LSM-tree.

### Running queries fast

Two techniques make scans over billions of values quick. **Vectorized** execution processes a batch of column values at a time in tight loops the CPU can run efficiently. **Query compilation** generates machine code for the specific query. Modern warehouses also separate the pieces: storage in open file formats on object storage, a query engine on top, and a catalog that tracks which files make up which table.

For queries that are run again and again, a **materialized view** stores the result so it does not have to be recomputed, at the cost of updating it when the data changes. A data cube is the same idea taken further: a grid of aggregates precomputed along several dimensions.

## Full-text and vector search

Searching text needs a different index. An **inverted index** maps each word to the list of documents containing it, so a search intersects a few lists instead of reading every document.

Keyword search fails when the query uses different words from the document. **Vector embeddings** address that: a model turns each document into a list of numbers such that documents with similar meaning end up close together, and a search finds the vectors nearest to the query's vector. A flat index compares the query with every vector, which is exact but slow. Approximate indexes trade a little accuracy for a lot of speed. One kind groups vectors into clusters and searches only the nearest clusters. Another, **HNSW**, builds a layered graph and walks it from coarse to fine. Lab 3 measures that trade.

## What the labs show

- **Lab 1** builds a small LSM-tree and counts how many files each read has to search, with and without Bloom filters and compaction.
- **Lab 2** shows what sorting does to run-length encoding and compares file sizes for the same data.
- **Lab 3** compares exact and approximate nearest-neighbour search on 50,000 vectors.
