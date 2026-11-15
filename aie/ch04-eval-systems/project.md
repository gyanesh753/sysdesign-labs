## Goal

Practise the three judgments this chapter asks of you: reading an evaluation result without being misled, choosing a model methodically, and doubting a benchmark score.

All three labs are plain Python and run instantly. The model names, scores and prices in lab 2 are invented.

## Lab 1: slices and sample size

```bash
python lab1_eval_pipeline.py
```

**What you should observe**

- Part A: version 2 of a support bot scores 93% against 90% on easy questions and 55% against 50% on hard ones, yet 66% against 82% overall. It was tested on 700 hard questions where version 1 had 200.
- Part B: two models whose true accuracies are 80% and 83%. With 50, 200 or 1,000 test examples their uncertainty ranges overlap, and with 200 the worse model even comes out ahead. Only at 5,000 are they clearly separated.
- Part C: detecting a 10-point difference takes roughly 250 examples per model, a 3-point difference nearly 2,800, and a 1-point difference about 25,000.

**Try**

1. Re-weight both versions in Part A to the same mix of easy and hard questions. Which one is ahead?
2. In Part B, compare the two models on the *same* examples and bootstrap the difference directly. Does that need fewer examples?

## Lab 2: model selection

```bash
python lab2_model_selection.py
```

**What you should observe**

- Step 1: three of six candidates are removed outright: one for latency, one for quality, one for a licence that forbids commercial use, even though that one has the second-best quality.
- Step 2: the three survivors are all on the frontier. None beats another on both quality and latency, so the choice depends on what you value.
- Step 3: at 2 dollars per million tokens and 1,500 tokens per request, the API is cheaper below about 72,000 requests a day, and a 6,500-dollar server is cheaper above it.

**Try**

1. Halve the API price, as often happens within a year. Where is the break-even now?
2. Add a requirement that data must not leave your servers. What is left, and what does the cheapest option cost at 5,000 requests a day?

## Lab 3: contamination

```bash
python lab3_contamination.py
```

A benchmark of 400 arbitrary facts about an imaginary system. The "model" has no understanding: it answers correctly only if it has seen the exact question. Sixty percent of the benchmark leaked into its training text.

**What you should observe**

- The headline score is 72%.
- Searching for shared 8-word sequences flags 240 questions as seen in training. The model scores 100% on those and about 25%, which is pure guessing, on the other 160.
- On brand-new questions it also scores about 25%.

**Try**

1. Lightly reword the leaked questions before training, for example by changing "under high load" to "when busy". Does the 8-word check still flag them? What does that tell you about its limits?
2. Reduce the leak to 10%. Would you notice the inflation from the headline score alone?

## Write up in NOTES.md

Record the Part A table from lab 1, the break-even from lab 2, and the three scores from lab 3. Then answer: for an application you might build, list its hard requirements and one criterion for each of the four groups in the lecture.
