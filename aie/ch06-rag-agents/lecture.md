## Two ways to give a model more to work with

A model knows only what was in its training data and what you put in the prompt. Two patterns extend that, and most serious applications use one or both.

**Retrieval-augmented generation**, usually shortened to RAG, fetches information relevant to each question and adds it to the prompt. **Agents** give the model tools, so that it can look things up and take actions. Both are ways of constructing the right context for the model, and context does for a foundation model what features did for classical machine learning.

## Retrieval-augmented generation

### The architecture

A RAG system has two parts. A **retriever** finds the pieces of information most relevant to a query in some store of documents. A **generator**, the model, writes the answer using what was retrieved.

It works in two phases. Ahead of time, documents are split into pieces and indexed. At query time, the retriever fetches the best matching pieces and they are placed in the prompt together with the question.

Now that models accept very long inputs, why not paste in everything? Three reasons. However large the limit, there is always more data than fits. Every token costs money and time on every request. And a model given a great deal of irrelevant material answers worse than one given a small amount of the right material.

### Term-based retrieval

The oldest approach matches on words. A document is relevant if it contains the terms of the query. A term counts for more if it appears often in that document and rarely elsewhere, which stops common words from dominating. BM25 is the standard scoring formula built on that idea. Lookups are fast because the system keeps an index from each term to the documents containing it.

Term-based retrieval is cheap, fast, needs no model, and is a strong baseline. It is especially good at exact identifiers such as product codes, error numbers and names. Its weakness is vocabulary: a question about "holiday" will not find a document that only says "annual leave".

### Embedding-based retrieval

The alternative matches on meaning. Every chunk is converted into an embedding and stored in a vector database. The query is embedded in the same way, and the system returns the chunks whose embeddings are closest.

Comparing a query with every stored vector is too slow for large collections, so vector databases use approximate methods that give up a little accuracy for a great deal of speed. Chapter 4 of the first part of this course measured that trade.

This approach finds relevant text that shares no words with the query. Its costs are the compute to embed everything, the storage for the vectors, and extra latency. It can also blur distinctions that depend on an exact string.

### Comparing and combining

Judge a retriever by two things. **Context precision**: of what it retrieved, how much was relevant? **Context recall**: of what was relevant, how much did it retrieve? Then weigh those against speed and cost.

The two approaches are often combined, which is called hybrid search. One common method runs both and merges their rankings, favouring documents that rank well in either. Another uses the cheap retriever to fetch a broad set of candidates and a more precise one to reorder them.

Combining is not automatically an improvement. In lab 1, merging a good embedding ranking with a poor keyword ranking gives a result worse than the embeddings alone. Measure on your own questions before adding machinery.

### Getting more out of retrieval

- **Chunking.** How you split documents matters more than most people expect. Small chunks are precise but can separate a fact from the sentence that gives it meaning. Large chunks keep context together but dilute relevance and use up the prompt. Overlapping neighbouring chunks reduces the damage at boundaries. Lab 2 measures all of this.
- **Reranking.** Retrieve more candidates than you need, then reorder them with a more accurate and more expensive method, and keep the best few.
- **Query rewriting.** In a conversation, the user's follow-up "what about the larger one?" means nothing by itself. A model first rewrites it into a complete question, and that is what gets retrieved against.
- **Contextual retrieval.** Before indexing, attach to each chunk some context about where it comes from: the document's title, a short summary, the questions it answers. A chunk that says "it must be serviced every 30 days" becomes findable once it says which machine.

### Beyond text

The same pattern applies to other data. For images, retrieve by captions or with a model that embeds images and text into the same space. For data in tables, the usual approach is different: the model writes a database query from the question, the query is executed, and the model composes an answer from the result.

## Agents

### What an agent is

An **agent** is anything that perceives its environment and acts on it. In this setting, a model is given a goal and a set of **tools**, and works towards the goal by repeatedly choosing a tool, looking at the result, and deciding what to do next. The environment and the tools together define what the agent can do. A coding agent's environment is a codebase and its tools are things like reading files and running tests.

Agents can do much more than a model alone. They are also harder to make dependable, because a task takes many steps and each step is a chance to go wrong.

### Tools

Tools fall into three groups.

- **Knowledge augmentation.** Tools that fetch information: a retriever, web search, a database query, an internal API.
- **Capability extension.** Tools that cover the model's weaknesses: a calculator, a code interpreter, a unit converter. A model is unreliable at arithmetic and a calculator is not.
- **Write actions.** Tools that change something: sending an email, updating a record, making a payment.

Write actions are what make agents valuable and what make them dangerous. A read can be repeated or ignored. A write may be impossible to undo. They need the safeguards from the previous chapter: limited permissions and human approval where the stakes are high.

### Planning

Given a goal, the agent has to work out a sequence of steps. A sound design separates this into stages: generate a plan, check that the plan is valid, and only then execute it. Checking first is cheap and avoids carrying out a plan that calls a tool that does not exist or cannot possibly meet the goal.

Models turn a plan into action through **function calling**: you describe each tool, its purpose and its parameters, and the model replies with the name of a tool and the arguments to pass. Your code runs the tool and returns the result. Plans need not be straight lines. Steps can run one after another, in parallel, conditionally, or in a loop.

### Reflection and error correction

A good agent checks its own work. After a step it can ask whether the result is what was expected, and after the whole task whether the goal was met. When something has gone wrong, it revises the plan and tries again. Interleaving reasoning, action and observation in this way makes agents much more robust. The cost is more model calls, more tokens and more waiting.

### Tool selection

More tools mean more capability, and more ways to choose badly. Descriptions of every tool use up the prompt, and a model with too many options picks the wrong one more often. Find the right set by experiment: remove a tool and see how much performance falls, look at which tools are used and which are constantly misused, and compare how different models handle the same set.

### How agents fail

- **Planning failures.** The plan uses a tool that does not exist, calls a real tool with the wrong parameters, or passes plausible but incorrect values. Or the plan is valid and simply does not achieve the goal, or ignores a constraint such as a budget.
- **Tool failures.** The right tool was called correctly and returned something wrong, or the result was misread.
- **Efficiency.** The task was completed but took far too many steps, too much money or too long.

Errors **compound**. If each step is right 95% of the time, a ten-step task succeeds only about 60% of the time. That is why agents need each kind of failure measured separately, validation at each step, and evaluation of the final outcome. Lab 3 works through the numbers.

:::checkpoint[An agent finishes its task correctly 60% of the time, and each run is about ten steps. A colleague suggests switching to a model that is slightly better per step. Is that likely to matter?]
Yes, more than it sounds. At ten steps, 60% overall corresponds to about 95% per step. Raising that to 98% gives about 82% overall. Small gains per step multiply across the task, and so do validation and retries that catch detectable mistakes.
:::

## Memory

A model keeps track of things in three ways.

- **Internal knowledge**, fixed at training time. It cannot be updated without changing the model.
- **Short-term memory**: the context of the current request. Fast to use, limited in size, and gone when the conversation ends.
- **Long-term memory**: external storage that the system reads from by retrieval and writes to as it goes, which persists across sessions.

A memory system decides what to keep. When a conversation outgrows the context, the simplest policy drops the oldest messages, which can lose the very instruction that mattered. A better one summarizes older material and keeps the summary. Long-term memory lets an assistant remember a user's preferences next week and keeps an agent consistent over a long task. It also raises the question of what to do when new information contradicts old.

## What the labs show

- **Lab 1** compares keyword search, a real embedding model and two ways of combining them on a small handbook.
- **Lab 2** varies chunk size and overlap on a generated manual and measures what the retriever can still find.
- **Lab 3** traces one agent task step by step, then simulates how per-step errors add up and what validation recovers.
