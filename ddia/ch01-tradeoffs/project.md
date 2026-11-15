## Goal

See two of the chapter's trade-offs with your own numbers: storage layout decides which workload is fast, and derived data is only as good as the process that keeps it current.

Both labs are plain Python, no Docker needed. They create `orders.db` and `orders.duckdb` in this folder (about 150 MB, ignored by git).

## Lab 1: row store vs column store

```bash
python lab1_row_vs_column.py
```

The script generates 2,000,000 orders, loads the same data into SQLite (rows) and DuckDB (columns), then times 5,000 lookups by `order_id` and one `GROUP BY country` aggregate on each.

**What you should observe**

- Point lookups: SQLite is far faster, on the order of tens of times.
- The aggregate: DuckDB is far faster, again on the order of tens of times.
- File size: the DuckDB file is several times smaller than the SQLite one.

Exact times depend on your machine. The direction and rough size of the gap should not.

**Try**

1. Drop the SQLite index (comment out the `CREATE INDEX` line) and rerun. What happens to point lookups, and why?
2. Change the aggregate to `SELECT * FROM orders ORDER BY price DESC LIMIT 10`. Does the column store still win by as much? Why would reading every column change the picture?

## Lab 2: derived data goes stale

```bash
python lab2_derived.py
```

Run lab 1 first; this one reuses `orders.db`. It builds a `daily_revenue` summary from `orders`, then updates one order and compares the summary with a fresh calculation from the source. Then it installs a trigger that adjusts the summary on every update, and updates the order again.

**What you should observe**

- After the first update, "source says" and "derived says" differ. The summary is stale.
- After the trigger is installed, the second update moves the summary by the right amount.
- The two numbers are still not equal at the end.

That last point is the lesson. The trigger keeps the summary in step from the moment it exists, but it does not repair the drift from the update that happened before. Only a rebuild from the source does. Incremental maintenance is fast; rebuilding is what makes it trustworthy.

**Try**

1. Call `rebuild()` at the end and confirm the two numbers match.
2. The trigger only handles `UPDATE`. Write the `INSERT` and `DELETE` versions. What goes wrong for an insert on a day and country that has no summary row yet?
3. Note that each run adds to the quantity of order 42, so the numbers change from run to run. Is this script idempotent? What would make it so?

## Write up in NOTES.md

Record your four timings and two file sizes from lab 1, and the three numbers from lab 2. Then answer in your own words: name one derived dataset in a system you have worked on, its system of record, and how it is kept current.
