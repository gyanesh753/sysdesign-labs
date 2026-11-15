## Beyond "it works"

Functional requirements say what a system does: store a post, show a timeline. Nonfunctional requirements say how well: how fast, how dependably, at what size, and how painful it is to change. They decide most architecture choices, and they are useless until you can put a number on them. This chapter gives the vocabulary for four of them: performance, reliability, scalability, and maintainability.

## A worked example: home timelines

Take a social network where users post short messages and follow each other. Assume, as rough working figures:

- 500 million posts a day, which is about 5,800 per second on average, with spikes far above that.
- The average user follows 200 accounts and has 200 followers. The spread is enormous: most accounts have few followers, a few celebrities have over 100 million.

The feature is the home timeline: recent posts from everyone you follow. There are two basic ways to build it.

### Fan-out on read

Store each post once. When a user opens their timeline, look up everyone they follow, fetch those accounts' recent posts, and merge them by time.

Writing is trivial. Reading is the problem. If 10 million users are online and each client checks for new posts every 5 seconds, that is 2 million timeline queries per second. Each one touches 200 followed accounts, so the database is doing around 400 million post lookups per second, and almost all of them find nothing new.

### Fan-out on write

Give every user a precomputed timeline, like a mailbox. When someone posts, insert that post into the timeline of each of their followers. Reading is now a single cheap lookup.

The work has moved to the write path. At 5,800 posts per second and 200 followers each, that is a little over a million timeline inserts per second. Large, but hundreds of times less than the read approach, because people read much more often than they post.

A precomputed timeline is derived data in the chapter 1 sense: a materialized view of posts and follows. It can be rebuilt from them, and it has to be kept in step with them.

### The celebrity problem

The average hides the worst case. One post from an account with 100 million followers means 100 million inserts. The usual answer is a hybrid: fan out on write for ordinary accounts, but store celebrity posts once and merge them in when a follower reads.

:::callout[The pattern to remember]
"Fan-out" is the number of downstream operations one request triggers. Averages describe your typical load. The skew, meaning the heaviest few users or keys, is what breaks the design.
:::

## Describing performance

Two measures matter for an online system:

- **Response time**: how long one request takes, as the client sees it.
- **Throughput**: how many requests (or how much data) the system handles per second.

They are linked. As throughput nears what the hardware can do, requests start queueing and response time climbs steeply.

### Response time and its parts

What the client experiences is the sum of several things:

- **Service time**: how long the server spends actively working on the request.
- **Queueing delay**: time spent waiting, for a free CPU, a connection, a lock.
- **Network latency**: time in transit in both directions.

Queueing is often the largest and least stable part. A server can only work on a few things at once, so a handful of slow requests can hold up the fast ones behind them. This is head-of-line blocking. It is also why response time should be measured at the client: the server's own timer does not see the time a request spent waiting to be picked up.

### Percentiles, not averages

Run the same request a thousand times and you get a thousand different times. So response time is a distribution, and the mean describes it badly. A few very slow requests pull the mean up, and it does not tell you how many users had a bad experience.

Use percentiles. Sort the response times:

- The **median** (p50) is the halfway point. Half of requests are faster, half slower.
- **p95, p99, p99.9** are the values that 95%, 99%, 99.9% of requests beat.

The high percentiles are called **tail latencies**. They matter more than their size suggests. The slowest requests often belong to the customers with the most data, who tend to be the most valuable. And a user loading one page usually makes many requests, so their chance of hitting a slow one is much higher than 1%.

Percentiles are also how targets get written down. A service level objective (SLO) might say: median under 200 ms and p99 under 1 s, measured over five minutes. A service level agreement (SLA) is the contract that says what happens if that is not met.

### Tail latency amplification

Suppose serving one user request needs calls to several backend services in parallel, and the request finishes when the slowest call returns. Even if each backend is slow only 1% of the time, the user request is slow whenever *any* of them is.

With `k` independent calls, the chance that at least one is slower than the single-call p99 is

```text
1 - 0.99^k
```

:::spoken
One minus zero point nine nine to the power of k.
:::

For 5 calls that is about 5%. For 20 calls about 18%. For 100 calls about 63%: the "rare" slow case is now the common one. Lab 2 measures exactly this.

### The averaging trap

Percentiles cannot be averaged. If one server reports a p99 of 60 ms and another 1,700 ms, the p99 of all their requests together is *not* the midpoint. It depends on how many requests each served. To combine percentiles across machines or time windows, merge the underlying data, in practice by adding histograms. Libraries such as HdrHistogram and t-digest exist for this.

:::checkpoint[A dashboard shows "p99 latency" as the average of each server's p99. A tiny, broken server reports 1.7 s; a hundred healthy ones report 60 ms. Is the dashboard's number meaningful?]
No. It is neither the p99 of all requests nor any other percentile. The broken server handles almost no traffic, so the true overall p99 is close to the healthy value, or it could be much worse if that server took more load. Only merging histograms tells you.
:::

## Reliability and fault tolerance

A reliable system keeps doing the right thing when things go wrong. Two words need separating:

- A **fault** is one part of the system misbehaving: a disk dies, a process crashes, a network link drops.
- A **failure** is the system as a whole no longer giving users the service they need.

A system is **fault-tolerant** if faults do not turn into failures. That is always tolerance of *specific* kinds of fault, up to some number. A part whose fault takes the whole system down is a single point of failure.

**Hardware faults.** Disks, memory, power supplies and whole machines fail routinely once you have enough of them. The answer is redundancy: spare disks, spare power, and above all spare machines, so that losing one does not stop the service. Tolerating the loss of a whole machine also lets you patch and restart nodes one at a time without downtime.

**Software faults.** Hardware faults are mostly independent. Software faults are not: the same bug sits on every node and can take them all down together, as can a shared dependency that slows down, or one failure that triggers the next. There is no single cure. Careful assumptions, testing, process isolation, letting processes crash and restart, and good monitoring all help.

**Human faults.** Configuration mistakes by operators cause a large share of outages. Blaming the person changes nothing. Design so that mistakes are hard to make and cheap to undo: sandboxes for experiments, gradual rollouts, fast rollback, clear monitoring, and incident reviews that look for what in the system made the mistake easy, without assigning blame.

Some teams deliberately inject faults in production (chaos engineering) to make sure the tolerance machinery actually gets exercised.

### When overload feeds itself

A system pushed past its capacity does not just get slower. Queues grow, response times pass the client's timeout, and clients retry. Now the server gets the original load plus the retries, while also spending effort on requests whose clients have already given up. That is a **retry storm**.

The dangerous part is that it can outlast its cause. Even after the original spike or slowdown ends, the system stays overloaded because the retries keep it there. This is a **metastable failure**: a bad state that holds itself in place. Often the only way out is to shed load or restart.

Defences, on both sides:

- Clients: wait longer between successive retries, with randomness added (exponential backoff with jitter), and stop calling a service that keeps failing for a while (circuit breaker).
- Servers: notice overload and reject requests early (load shedding), or tell clients to slow down (backpressure).

Lab 3 simulates this and shows which defences are enough.

## Scalability

Scalability is not a yes/no property. The useful question is: if load grows in this particular way, what are our options for coping?

First describe the load with a few numbers that fit your system: requests per second, read/write ratio, active users, and whatever your fan-out is. Then ask what happens to performance when one of them doubles with the same resources, and how much you must add to keep performance the same.

Three hardware shapes:

- **Shared-memory** (scale up, vertical): one bigger machine. Simple, but cost rises faster than capacity and there is a ceiling.
- **Shared-disk**: several machines with their own CPU and memory, sharing storage over a fast network.
- **Shared-nothing** (scale out, horizontal): many independent machines coordinating over an ordinary network. It can scale close to linearly and survives the loss of a machine or a datacenter, at the price of the distributed-systems complexity from chapter 1.

Two principles hold up well. Break the system into parts that can work mostly independently. And do not make it more complicated than the load in front of you needs: an architecture built for a hundred times your current load is usually wrong for today and wrong again by the time you get there.

## Maintainability

Most of the cost of software comes after it first ships: fixing, operating, adapting, and repaying shortcuts. Three properties keep that cost down.

- **Operability**: make it easy to keep running. Good monitoring, automation, no dependence on one particular machine, sensible defaults, predictable behaviour, clear documentation.
- **Simplicity**: make it easy to understand. Complexity that comes from the problem is unavoidable; complexity that comes from the implementation is not. The main tool is a good abstraction that hides detail behind a clean interface.
- **Evolvability**: make it easy to change. Requirements always move. Systems that are simple, loosely coupled and reversible in their decisions are easier to move with them.

## What the labs show

- **Lab 1** builds the timeline three ways on a skewed follow graph and times the write and read path of each.
- **Lab 2** shows mean versus percentiles, measures tail amplification against the formula, and demonstrates the averaging trap.
- **Lab 3** simulates a brief slowdown under three retry policies and shows a system that never recovers on its own.
