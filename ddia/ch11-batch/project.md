## Goal

Do one batch task three ways on a single machine, then build the core of a distributed batch engine small enough to read in one sitting.

Both labs are plain Python. Lab 1 also calls the standard Unix tools `awk`, `sort`, `uniq` and `head`, which are on every Mac. No Docker needed.

## Lab 1: the top five pages

```bash
python lab1_log_analysis.py
```

The script writes a 400,000-line web log to a temporary folder, with about 50,000 distinct pages and a few very popular ones, then finds the five most requested pages three ways.

**What you should observe**

- All three methods give the same five pages and counts; the script asserts it.
- The hash table is the fastest here. It has to hold one counter for each of the 50,000 distinct pages.
- The sort-and-merge version is a little slower but only ever holds one chunk of 50,000 lines in memory, and it would behave the same on a log a thousand times larger.
- The Unix pipeline is the slowest of the three on this small input and by far the least code.

**Try**

1. Raise `PAGES` to 5,000,000 and `LINES` to 10,000,000. Watch memory use for the hash table version. Which method would you trust on a machine with 4 GB of memory?
2. Change the question to "the five IP addresses with the most requests". How much of each solution has to change?

## Lab 2: a minimal MapReduce

```bash
python lab2_mapreduce.py
```

`run_job` is the whole engine: a map phase with one task per input split, a shuffle that partitions by key and sorts, and a reduce phase. The workflow joins 40,000 page views to 2,000 users by user ID, then counts views per country in a second job.

**What you should observe**

- Run 1 takes 10 task attempts and prints a count for each of the five countries.
- In run 2, one map task is killed halfway. Its partial output is dropped, the task runs again, and the totals are identical to run 1. The script asserts this.
- A one-line SQL query gives the same answer, also asserted.

Read `join_mapper` and `join_reducer` closely. The trick of tagging user records so they sort ahead of the views is what lets the reducer work in a single pass.

**Try**

1. Change the engine so that a failed task's partial output is *not* discarded. How wrong are the totals?
2. Make the mapper nondeterministic, for example by dropping a random 1% of records. Is a retry still safe? What would you see?
3. Add a third job that finds the most viewed page per country.

## Write up in NOTES.md

Record the three timings from lab 1 and the country counts from lab 2. Then answer: name one dataset in a system you know that is rebuilt by a batch job. What happens if that job produces bad output?
