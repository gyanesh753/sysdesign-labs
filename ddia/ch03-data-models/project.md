## Goal

Feel the trade-offs between data models by running the same questions against the same data stored in different shapes.

Both labs are plain Python with an in-memory SQLite database. No Docker needed, and each runs in a few seconds.

## Lab 1: documents versus tables

```bash
python lab1_document_vs_relational.py
```

The script creates 20,000 profiles, each with one to four jobs at one of 200 organizations. It stores them twice: as normalized tables (`users`, `positions`, `orgs`) and as one JSON document per profile with the organization name copied in.

**What you should observe**

- Task 1, loading whole profiles: the document version is somewhat faster. It is one read against two queries and a join.
- Task 2, renaming one organization: the relational version changes exactly 1 row. The document version has to rewrite a few hundred documents.
- Task 3, who worked at one organization: the relational version is an index lookup. The document version scans every document and is around a hundred times slower.

The pattern is the point. Documents win when you read the tree as a whole, and lose as soon as the question cuts across documents.

**Try**

1. Interrupt the document rename halfway (add a `break` after 100 rewrites). How would a reader know which name is correct?
2. Store the organization ID in the documents instead of the name. Which task gets better and which gets worse?

## Lab 2: graph queries

```bash
python lab2_graph_queries.py
```

The script builds a graph of places nested to different depths, 3,000 people with a birthplace and a home, and a "knows" network. Everything lives in two tables, `vertices` and `edges`.

**What you should observe**

- Query 1 returns the same set of people from the recursive SQL and from the graph traversal; the script asserts this. The SQL takes about 70 words.
- Cities sit between 2 and 5 hops below their continent, which is why no fixed number of joins could answer the question.
- Query 2: the number of people reachable roughly triples with each extra hop, because everyone knows three others.

**Try**

1. Write Query 1 without `WITH RECURSIVE`, using a fixed chain of joins. How many levels do you need, and what happens when a deeper place is added?
2. Add a `since` property to the "knows" edges and count only friendships formed after a given year.

## Write up in NOTES.md

Record the three pairs of timings from lab 1 and the reach counts from lab 2. Then answer: pick a dataset you know, and say which relationships in it are one-to-many and which are many-to-many.
