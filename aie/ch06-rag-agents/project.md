## Goal

Build the retrieval half of a RAG system in miniature and measure it, then look at what makes multi-step agents fragile.

Lab 1 uses an embedding model through Ollama (`nomic-embed-text`). Labs 2 and 3 are plain Python.

## Lab 1: three retrievers

```bash
python lab1_retrieval.py
```

A made-up company handbook of 26 one-sentence entries, including several with look-alike codes. Twelve questions: six ask by meaning in words the handbook does not use, six contain an exact code. Each cell shows how often the right entry was ranked first, and how often it was in the top three.

**What you should observe**

In my run, with one particular embedding model:

- Keyword search ranks the right entry first for every question that contains a code, and for none of the questions asked by meaning.
- The embedding model gets five of six meaning questions right at rank one and all six in the top three. It also gets every code question right, including the look-alike codes.
- Merging the two rankings with equal weight is much worse than embeddings alone on meaning questions. Weighting the embedding ranking three times as heavily helps and still does not catch up.

On this collection the embedding model simply wins. The honest conclusions are that keyword search costs almost nothing and is exact on identifiers, and that combining two retrievers only helps when each is good at something the other is not. With thousands of near-identical codes, or a weaker embedding model, the balance shifts.

**Try**

1. Add 200 more entries with codes that differ from each other by one character. Does the embedding model still get every code right?
2. Use keyword search only when the query contains a code-like token, and embeddings otherwise. How does that simple router score?

## Lab 2: chunking

```bash
python lab2_chunking.py
```

A generated manual with one section per machine. Each section says how often the machine must be serviced and, in the next sentence, what happens if that is missed. The second sentence does not name the machine.

**What you should observe**

- Chunks of 12 words find the service interval only half the time and never find the interval together with the consequence.
- Chunks of 25 or 60 words find the pair about three times in four. With an overlap of 20 words, 60-word chunks find it every time.
- Chunks of 250 or 1,000 words also find everything, but send the model 750 or 3,000 words for a one-line question.

**Try**

1. Split on sentence boundaries instead of a fixed number of words. Does that help without overlap?
2. Prefix every chunk with the name of its section before indexing. Which row improves most?

## Lab 3: an agent loop

```bash
python lab3_agent_loop.py
```

**What you should observe**

- Part A: a refund task takes four tool calls. The last is a write action and is marked as needing human approval.
- Part B: with 95% accuracy per step and no checks, success falls from 95% for one step to 77% for five, 61% for ten and about 35% for twenty. Validating each call and allowing a retry raises the ten-step figure to about 81%.
- Part C: to complete a ten-step task 90% of the time, each step has to be right 99% of the time.

**Try**

1. Change the share of mistakes a validator can detect from 60% to 90%. How much of the gap closes?
2. Add a tool that returns a wrong answer 2% of the time even when called correctly. Which of the three failure types in the lecture is that?

## Write up in NOTES.md

Record the table from lab 1 with the embedding model's name, the table from lab 2, and Part B from lab 3. Then answer: for a document collection you know, what would a chunk need to carry with it to be understandable out of context?
