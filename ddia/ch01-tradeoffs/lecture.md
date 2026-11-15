## There is no best design

Almost every question in data systems has the answer "it depends". This chapter does not teach a technology. It maps the forks in the road you hit on every project, so that when you pick a side you know what you are giving up.

Four forks matter most:

| Fork | One side | Other side |
|---|---|---|
| Workload | Operational: serve users now | Analytical: understand the business |
| Role of a dataset | System of record | Derived data |
| Who runs it | Cloud service | Self-hosted |
| Shape | Single node | Distributed |

:::spoken
The four forks are: operational versus analytical workloads, system of record versus derived data, cloud service versus self-hosted, and single node versus distributed.
:::

A fifth concern cuts across all of them: the data is about people, so law and ethics constrain the design.

## Operational versus analytical systems

### Two workloads, two shapes

An **operational** system is the backend of an application. It handles requests from users or other services: look up this order, add that item to the cart. Each request touches a handful of records, usually found by key, and must finish in milliseconds. The classic name is OLTP, online transaction processing.

An **analytical** system answers questions for analysts and decision makers: revenue per country last quarter, which signup flow converts better. Each query scans a huge number of records but reads only a few columns of each and returns an aggregate. The classic name is OLAP.

| | Operational (OLTP) | Analytical (OLAP) |
|---|---|---|
| Typical read | A few rows, fetched by key | Aggregate over very many rows |
| Typical write | Create, update, delete single records | Bulk import or event stream |
| Who uses it | End users, through an application | Analysts and data scientists |
| Queries | Fixed, written by the developers | Ad hoc, written on the spot |
| Data holds | Current state | History of what happened |
| Size | Gigabytes to terabytes | Terabytes to petabytes |

:::spoken
The table on the page compares the two side by side. In short, operational systems fetch a few rows by key, hold the current state, and run fixed queries written by developers. Analytical systems aggregate over very many rows, hold history, and run ad hoc queries written by analysts.
:::

These differences are large enough that one storage engine rarely does both well. Row-oriented storage keeps all fields of a record together, which is ideal when you fetch one whole record by key. Column-oriented storage keeps each column together, which is ideal when a query reads two columns out of fifty across a billion rows. Lab 1 lets you measure this on your own machine.

:::checkpoint[A dashboard query takes 40 seconds on the production Postgres and slows down checkout while it runs. Which workload is in the wrong place?]
The analytical one. An ad hoc scan over history is competing for the same resources as short key lookups that users are waiting on. Moving it to a separate analytical copy protects the operational system.
:::

### Warehouses and lakes

Because the workloads fight each other, companies copy operational data into a separate system built for analysis.

A **data warehouse** is a read-mostly database holding a cleaned copy of data from many operational systems. Getting data in is called **ETL**: extract it from the sources, transform it into a schema that suits analysis, load it into the warehouse. Analysts then query it with SQL without touching production.

A warehouse forces everything into a relational model up front. Data scientists often want the raw material instead: text, images, event logs, features for training. A **data lake** is a central store, usually cheap object storage, that keeps files in whatever format they arrived in. Structure is applied later by whoever reads it.

Some databases advertise hybrid transactional/analytical processing (HTAP), handling both workloads in one product. That helps when the same application needs both kinds of query on fresh data. It does not remove the need for a warehouse, because a warehouse's real job is combining data from *many* separate operational systems.

Data also flows back. The output of analysis, such as a recommendation model or a fraud score, gets loaded into operational systems to serve users. So the picture is a loop, not a one-way pipe.

## Systems of record and derived data

A second way to classify any dataset in your architecture:

- A **system of record** (source of truth) holds the authoritative version. New facts are written here first, each fact stored once.
- **Derived data** is the result of taking existing data and transforming it. If you lose it, you can rebuild it from the source.

Caches, search indexes, materialized views, denormalized tables, warehouse tables, and trained models are all derived. They are redundant on purpose: they repeat information you already have in a form that makes some read fast.

The distinction is not a property of a tool. The same Postgres can be the source of truth for one table and hold a derived summary in another. It is a property of how *you* use the data, and stating it clearly is what keeps a large architecture understandable: for every dataset you should be able to say where it comes from and what happens when the source changes.

The cost of derived data is keeping it in step. The moment the source changes, every derived copy is stale until something updates it. Lab 2 shows this happening and one way to fix it.

:::callout[Rule of thumb]
If two stores disagree, the system of record wins and the derived one gets rebuilt. If you cannot say which is which, you have a design problem, not a data problem.
:::

## Cloud versus self-hosting

For anything you need, you can write it, run open source yourself, or pay a provider to run it. This is ultimately a business question: what should your organization spend its attention on?

Reasons to use a cloud service:

- You start faster, and you do not need in-house expertise for each system.
- Load that varies a lot is cheaper when you can add and remove capacity on demand.
- The provider operates the same service for many customers and is often better at it than you would be.

Reasons to hesitate:

- You cannot change it, and you can see very little when it misbehaves. During an outage you wait.
- If the provider raises prices or drops the product, moving is expensive.
- Your data sits with a third party, which matters for security and for regulation.
- For steady, predictable load, renting can cost more than owning.

### Separating storage from compute

Software designed for the cloud looks different from software moved to it. A traditional database assumes a machine with local disks that it owns. A **cloud-native** system is built from other cloud services: it keeps data in an object store and treats compute nodes as disposable.

That is **separation of storage and compute**. Storage is a shared, durable service; query processing runs on machines that can be added, removed, or replaced without moving data. You can scale the two independently, and an idle system can shrink its compute to nothing while the data stays put. The price is that every read crosses a network, so these systems cache aggressively on local disk.

Operations change too. The job shifts from nursing individual machines to choosing services, wiring them together, automating, and watching cost. Capacity planning becomes financial planning.

## Distributed versus single-node

A system spread over several machines that talk over a network is distributed. Good reasons to build one:

- **The problem is distributed anyway.** Two phones messaging each other are separate machines no matter what you do.
- **Fault tolerance.** If one machine dies, another takes over.
- **Scale.** The data or load exceeds one machine.
- **Latency.** Users worldwide are served from a region near them.
- **Elasticity.** Capacity follows demand up and down.
- **Law.** Some data must stay in a particular country.

The cost is real. Every network call can fail or time out, and when it times out you do not know whether the other side did the work. Calling a function becomes slower by orders of magnitude. Debugging needs tracing across services. Keeping data consistent across nodes is hard enough to fill several later chapters.

So the advice is plain: if one machine can do the job, use one machine. Hardware has grown faster than most datasets, and single-node engines such as DuckDB and SQLite handle workloads that needed a cluster fifteen years ago.

### Microservices and serverless

Splitting an application into services, each with its own database and its own team, is mostly a solution to a *people* problem. Teams can release independently and the boundaries are explicit. For a small team it mainly adds network hops, deployment work, and failure modes.

Serverless (functions as a service) goes one step further: you hand over code, the provider decides when and where to run it, and you pay for execution time. The same idea applied to databases is what makes "scale to zero" possible.

:::checkpoint[Your team of four is asked to split a working monolith into twelve microservices "for scalability". What question should you ask first?]
Whether one machine, or one service scaled out behind a load balancer, cannot already handle the load. Microservices mainly buy independent deployment for many teams. A team of four pays the distributed-systems cost without that benefit.
:::

## Data, law, and society

Data systems hold information about people, and regulators have noticed. Privacy laws such as the GDPR give people rights over their data, including having it deleted. That sounds simple until you remember derived data: a deleted user must also disappear from the cache, the search index, the warehouse, the backups, and arguably from models trained on them. Systems built on immutable, append-only logs need a deliberate plan for erasure.

Two habits help. Collect less (data minimization): data you never stored cannot leak and does not need deleting. And count the cost of keeping data, not only the value, when deciding what to retain.

## What the labs show

- **Lab 1** loads the same two million orders into a row store (SQLite) and a column store (DuckDB) and times a key lookup and an aggregate on each. Expect each engine to win clearly at its own workload, and the column file to be several times smaller.
- **Lab 2** builds a derived summary table, changes the source, and shows the two disagreeing. A trigger then keeps them in step, with one catch worth finding yourself.
