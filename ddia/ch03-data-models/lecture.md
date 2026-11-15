## Why the data model matters

A data model is the shape you give your data: tables, documents, or a graph. It is the most consequential choice in an application, because it decides which questions are one line to ask and which need pages of code. Each model carries an assumption about how the data will be used. This chapter is about matching the model to the relationships in your data.

One idea runs through all of it. In a **declarative** query language such as SQL you state what result you want, not the steps to get it. That leaves the database free to pick an index, reorder joins, or run parts in parallel, and to get better at it without your queries changing.

## Relational versus document

### The object-relational mismatch

Application code works with objects that nest: a profile contains a list of jobs, each job has a title. Relational tables are flat, so that profile is spread over several tables and has to be reassembled with joins. The awkward translation layer between the two is called the impedance mismatch. Object-relational mappers hide some of it, but they can also hide expensive behaviour, such as quietly issuing one query per item in a list.

### One-to-many: where documents fit

A profile with its jobs is a tree: one parent, many children, and you usually want all of it at once. A **document** model stores that tree as one JSON record. You fetch it with a single read, it matches the object in your code, and the related pieces sit together on disk. That locality only pays off when you need most of the document most of the time, and when documents stay reasonably small.

### Many-to-one and many-to-many: where they strain

Now suppose many profiles refer to the same organization. You have two options. Copy the organization's name into every profile, or store it once and keep only its ID in each profile.

- Storing it once is **normalization**. A rename is one write and can never be half done. Reading needs a join.
- Copying it is **denormalization**. Reads are fast and need no join. A rename must find and rewrite every copy, and until it finishes the data disagrees with itself.

Neither is right in general. Normalized data is cheaper to write and keep correct; denormalized data is cheaper to read. The home timelines in chapter 2 were a deliberate denormalization. A useful rule: anything a human might want to change later should be referenced by an ID that itself never needs to change.

Analytics has its own conventions here. A star schema keeps one large fact table of events surrounded by small dimension tables that describe who, what and where.

### Schema on read, schema on write

Document databases are often called schemaless, which is misleading. The code that reads the data still assumes a structure. The difference is when it is enforced: a relational database checks it when data is written, a document database leaves it to whoever reads. The second is handy when records are varied or the structure is set by someone else. The first catches mistakes earlier.

The two families have been converging. Relational databases store and index JSON; document databases have gained joins. Using both styles in one database is now normal.

:::checkpoint[An online shop stores each order as one document, with the product names copied into it. A product is later renamed. Should old orders change?]
Probably not. An order records what was bought at the time, so the copied name is a fact about the past and not a stale copy. Denormalization is only a problem when the copy is supposed to track the original.
:::

## Graph models

When many-to-many relationships are everywhere and anything can link to anything, the natural model is a graph: **vertices** for things and **edges** for relationships. Social networks, road maps and the web all look like this, and one graph can mix very different kinds of things.

### Property graphs

In a property graph each vertex has an ID, a label and a set of properties. Each edge has a start vertex, an end vertex, a label saying what kind of relationship it is, and its own properties. You can store this in two relational tables, one for vertices and one for edges, with indexes so edges can be followed in both directions. Nothing restricts which kinds of things can be connected, which makes graphs easy to extend.

### Querying a graph

The trouble with plain SQL is that you often do not know how many hops a path needs. A city might be inside a region inside a country inside a continent, or the nesting might be shallower. Graph query languages such as Cypher let you say "follow this kind of edge zero or more times":

```text
MATCH (p:Person)-[:BORN_IN]->()-[:WITHIN*0..]->(:Place {name: 'Asia'}),
      (p)-[:LIVES_IN]->()-[:WITHIN*0..]->(:Place {name: 'Europe'})
RETURN p.name
```

:::spoken
The query on the page finds every person whose birthplace is somewhere within Asia and whose current home is somewhere within Europe, following the "within" edge as many times as needed.
:::

SQL can express the same thing with a recursive common table expression, but it takes several times as much text. Lab 2 runs both and checks that they agree.

Two other graph traditions are worth knowing by name. Triple stores hold everything as subject, predicate, object statements and are queried with SPARQL. Datalog builds complex queries from small rules that can refer to each other, which makes recursion natural.

GraphQL, despite the name, is not a graph database language. It is a way for a client, such as a mobile app, to ask a server for exactly the nested fields a screen needs. It is deliberately restricted so that untrusted clients cannot run arbitrarily expensive queries.

## Event sourcing and CQRS

So far the data model described current state. An alternative is to store what happened. With **event sourcing** every change is recorded as an immutable event in an append-only log, written in the past tense: seat reserved, booking cancelled. The log is the system of record.

You do not query the log directly. You derive read-optimized views from it, called materialized views or read models, and you can keep several views of the same events for different purposes. Separating the write model from the read models is known as CQRS.

The benefits: events say why something changed, not only what the result was; a new view can be built later by replaying history; and a bug in a view is fixed by correcting the code and rebuilding. The costs: replay must be deterministic, so anything looked up from outside has to be recorded in the event; and an immutable log sits awkwardly with a legal duty to delete personal data.

## DataFrames and arrays

Data scientists mostly work with DataFrames: tables manipulated through code, with operations a relational database lacks, such as reshaping rows into columns. Their usual destination is a matrix of numbers for statistical or machine learning code, which means turning categories into numeric columns. Scientific data such as images and sensor grids fits multidimensional arrays, and there are databases built for that too.

## What the labs show

- **Lab 1** stores the same 20,000 profiles both ways and times three tasks: loading a whole profile, renaming an organization, and asking who worked at one organization.
- **Lab 2** stores a graph in two tables and answers the same questions with recursive SQL and with a graph library.
