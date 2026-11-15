## Goal

See the mechanisms of this chapter working at small scale: what a read costs in an LSM-tree, what sorting does to a column, and what an approximate index gives up.

All three labs are plain Python and finish in a few seconds. No Docker needed.

## Lab 1: a tiny LSM-tree

```bash
python lab1_lsm.py
```

The script implements a memtable, immutable sorted runs, a Bloom filter per run, and a full compaction, then writes 200,000 values across 50,000 keys and reads back keys that exist and keys that do not.

**What you should observe**

- The writes produce 97 SSTables holding about four times as many entries as there are live keys. That ratio is the space wasted on overwritten values.
- Without Bloom filters, a read for a missing key searches all 97 files, and a read for an existing key searches about 24.
- With Bloom filters, both drop to between one and about two files. After compaction, an existing key costs one search and a missing key almost none.
- Compaction brings the stored entries back down to the number of live keys.

**Try**

1. Change `bits_per_key` from 10 to 4. How many files does a missing-key read search now? What did you save?
2. Add a `delete(key)` that writes a tombstone, and make `compact()` drop it. Why can a tombstone only be dropped when all older files are part of the merge?
3. Replace the single big compaction with one that merges only the four newest files. What happens to read cost over time?

## Lab 2: column compression

```bash
python lab2_column_compression.py
```

**What you should observe**

- Sorted by country and day, the `country` column needs 6 runs instead of over 400,000, and `day` needs 2,190. The `product_id` column is not helped at all, because only the leading sort columns form long runs.
- File sizes: uncompressed columns with no encoding are larger than the CSV, since every number takes a full 8 bytes. Dictionary and run-length encoding cut that to under a third, sorting helps a little more, and general-purpose compression roughly halves it again.
- In the sorted file, `country` takes about 1 kB and `day` about 14 kB, while `order_id`, which is unique per row, takes over 4 MB.
- The aggregate runs roughly twenty times faster from the column file than from CSV.

**Try**

1. Sort by `product_id` first instead. Which columns shrink now, and which grow?
2. Drop `order_id` from the file. What fraction of the total size was it? What does that say about high-cardinality columns?

## Lab 3: vector search

```bash
python lab3_vector_index.py
```

**What you should observe**

- The flat index is exact and takes a couple of milliseconds per query on 50,000 vectors.
- HNSW answers in hundredths of a millisecond. With the smallest search setting it finds about 89% of the true top ten; raising the setting brings recall to essentially 100% while staying far faster than the flat scan.

**Try**

1. Raise `N` to 200,000. How do the flat and HNSW query times scale?
2. Lower `M` to 4. What happens to recall at each `ef`?

## Write up in NOTES.md

Record the read-cost table from lab 1, the file sizes from lab 2 and the recall table from lab 3. Then answer: for a workload you know, would you pick an LSM-tree or a B-tree, and what would you measure to check?
