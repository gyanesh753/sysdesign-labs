## Three kinds of system

It helps to sort systems by how they are driven. A **service** waits for a request and answers as fast as it can; what matters is response time. A **batch** system takes a large, fixed set of input, works through all of it, and produces output; nobody is waiting, and what matters is throughput. A **stream** system sits in between, processing input shortly after it arrives. That is the next chapter.

Batch processing is the oldest of the three and still does a large share of the heavy lifting: building search indexes, training models, loading warehouses, producing reports. It rests on a small number of good ideas, and the first of them is fifty years old.

## Batch processing with Unix tools

Suppose you have a web server log and want the five most requested pages. On any Unix system you can chain a few small programs: one extracts the page from each line, one sorts, one collapses repeated lines into counts, one sorts by count, one keeps the first five. It takes a minute to write and handles gigabytes without complaint.

This works because of a few design habits worth copying:

- **Each tool does one thing.** Sorting is one program, counting duplicates another.
- **A uniform interface.** Every tool reads a stream of text and writes a stream of text, so any tool can feed any other.
- **Inputs are left alone.** Running the pipeline does not change the log file. You can run it again, or change one step and compare, without fear.
- **You can stop anywhere.** Cut the pipeline short and look at the intermediate output to see what went wrong.

### Sorting or hashing

There are two ways to count how often each page appears. Keep a hash table with one counter per distinct page, or sort the lines so identical pages are next to each other and count the runs.

The hash table is faster while it fits in memory. Its size depends on the number of distinct keys, not the number of lines. Sorting has no such limit: a good sort handles more data than memory by sorting chunks, writing them to disk, and merging the sorted chunks, which is sequential work that disks do well. Lab 1 runs both. Large-scale batch systems use exactly the same sort-and-merge idea, spread across machines.

The limit of Unix tools is that they run on one machine. Everything that follows is about lifting that limit.

## Storage for large batches

A batch system needs somewhere to keep very large files that survive machine failures. There are two answers. A **distributed filesystem** spreads the blocks of each file across many machines and keeps several copies, or uses an encoding that can rebuild lost blocks. An **object store**, the usual choice in the cloud, offers a simpler interface: put a whole object, get it back, list objects. Objects cannot be modified in place, which fits batch processing well, since its files are written once and then only read.

The other thing to notice is that storage and computation are separate, as in chapter 1. The machines that process the data need not be the ones that hold it.

## Running jobs on many machines

A batch job is split into **tasks** that can run in parallel, one per chunk of input. Getting those tasks to run on a shared cluster needs three things: a component on each machine that starts tasks and reports on them, a resource manager that knows which machines have spare capacity, and a scheduler that decides which job gets resources next.

### Handling faults

With thousands of machines, something fails during most large jobs. And failure is not only hardware. To use a cluster efficiently, low-priority batch tasks are often run on capacity that can be taken away at short notice when something more important needs it.

Batch systems cope with this simply, and the reason they can is the central idea of the chapter. Input files are **immutable**, and each task is a **deterministic** function of its input. So if a task fails or is evicted, you discard whatever partial output it produced and run it again, on any machine, and you get the same result. Nothing needs to be rolled back because nothing was changed.

The same property protects you from your own mistakes. If a job has a bug and writes bad output, you fix the code and run it again. The input is untouched. Compare that with a bug that writes bad data into a live database.

:::checkpoint[A batch job that has been running for three hours loses one of its 500 machines. What has to be redone?]
Only the tasks that were running on that machine, and anything whose output was stored only there. Because inputs are immutable and tasks are deterministic, each one can simply be run again elsewhere and will produce the same output.
:::

## Batch processing models

### MapReduce

The model that made large-scale batch processing mainstream has three steps:

1. **Map.** A function you write is called once for every input record. It emits any number of key-value pairs.
2. **Shuffle.** The framework brings together all pairs with the same key, by sorting. Pairs are routed by a hash of the key so that one key always goes to one place.
3. **Reduce.** A second function you write is called once per key, with all the values for that key, and produces output.

You write only the two functions. The framework handles splitting the input, running tasks in parallel, moving data and retrying failures. The cost is that one MapReduce job does very little, so real work needs many jobs chained into a workflow, each writing its full output to storage for the next to read.

### Dataflow engines

Newer engines keep the idea and remove the rigidity. A job is a graph of operators, with data flowing from one to the next, and sorting only happens where an operator needs it. Intermediate results can stay in memory or on local disk. If some are lost, the engine recomputes only the pieces that depend on them. The result is much faster and much less code.

### Joins and grouping

How do you join two huge datasets when neither fits in memory? Use the shuffle. Suppose you have page views and user profiles and want views per country. Key both datasets by user ID. The shuffle then delivers each user's profile and all of that user's page views to the same place, and combining them is trivial. This is a **sort-merge join**. Grouping works the same way: key by whatever you are grouping on.

### Query languages and DataFrames

Hardly anyone writes map and reduce functions by hand any more. You write SQL, or use a DataFrame API, and a query optimizer turns it into a plan of operators. That is the lesson of chapter 3 again: say what you want and let the system decide how. Meanwhile data warehouses have learned to run long, fault-tolerant queries over files in object storage, so the line between a batch engine and a warehouse has largely faded.

## Batch use cases

- **Extract, transform, load.** Moving data from operational systems into a warehouse or lake, cleaning and reshaping it on the way.
- **Analytics.** Reports and aggregates computed on a schedule, as well as one-off exploratory queries.
- **Machine learning.** Turning raw data into features, training models, and scoring large numbers of records in bulk.
- **Derived data for services.** Search indexes, recommendation lists and lookup tables are often built by a batch job and then served to users.

For the last of these, how the output reaches the serving system matters. Writing to a live database one record at a time from inside the job is slow, can overwhelm the database, and breaks the retry property, because a retried task would write again. The better pattern is to have the job build complete files, and then load them into the serving system in bulk, replacing the old version in one step. If the new data is bad, you switch back to the old.

## What the labs show

- **Lab 1** finds the top pages in a 400,000-line log with Unix pipes, with a hash table, and with a hand-written sort-and-merge, and checks that all three agree.
- **Lab 2** implements MapReduce in about forty lines, uses it to join and count, kills a task halfway, and compares the result with SQL.
