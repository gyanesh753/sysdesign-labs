## Goal

Assemble the components around a model in miniature, find out how a semantic cache really behaves on a real embedding model, and practise distrusting feedback.

Labs 1 and 3 are plain Python. Lab 2 uses an embedding model through Ollama (`nomic-embed-text`). Prices, latencies and failure rates in lab 1 are invented.

## Lab 1: the pieces around a model

```bash
python lab1_gateway.py
```

**What you should observe**

- Part A: an email address and a phone number are replaced with placeholders before the text is sent to the model, and restored in the reply shown to the user.
- Part B: sending 20,000 requests to the large model costs 240 dollars with an average latency of 2.1 seconds. Routing simple questions to a small model brings that to about 51 dollars and 0.74 seconds. An exact cache brings it to about 7 dollars, because 97% of this traffic repeats. Both together cost about 2 dollars.
- Part C: with a fallback provider, failures fall from about 30 in a thousand to about 1.4 in a thousand.

The cache looks spectacular here because the simulated traffic is very repetitive. Measure how much your real traffic repeats before expecting the same.

**Try**

1. Make the router wrong 10% of the time, sending hard questions to the small model. What else would you now need to measure besides cost?
2. Change the traffic so that only a fifth of requests are repeats. Which component matters most then?

## Lab 2: a semantic cache

```bash
python lab2_semantic_cache.py
```

Eight pairs of questions that mean the same thing, and eight pairs that look alike and need different answers, such as upgrading against downgrading a plan.

**What you should observe**

In my run, with one embedding model:

- Same-meaning pairs have similarities between 0.85 and 0.94. Look-alike pairs fall between 0.82 and 0.94. The two ranges almost coincide.
- At a threshold of 0.95 nothing is served from the cache. At 0.90 half of the same-meaning questions are served, and one in eight look-alikes gets a wrong answer. At 0.85 nearly all same-meaning questions hit, and so do nearly all the look-alikes.
- The most confusable pair is Android against iPhone, at 0.94.

There is no threshold here that gives useful hits without wrong ones. That is a property of this model and these questions, and it is the reason a semantic cache has to be tested on your own traffic before it is trusted.

**Try**

1. Add a check after a cache hit: ask a small model whether the two questions would have the same answer. How would that change cost and latency?
2. Write five more look-alike pairs from a product you know. Where do they fall?

## Lab 3: feedback

```bash
python lab3_feedback_signals.py
```

**What you should observe**

- Part A: two versions whose answers are truly good 70% and 80% of the time. Thumbs ratings arrive from about 3% of conversations and say 81% and 87%. Satisfaction inferred from behaviour says about 66% and 76%: nearer the truth, and the gap between versions is clear.
- Part B: two identical models. When one is always shown first, it wins 60% of comparisons. With the order randomized it wins 50%.
- Part C: twenty equally good items. Always showing the most-clicked one gives a single item all the clicks, and only that item is ever shown enough to judge. Showing a random item a fifth of the time means all twenty get enough exposure to compare.

**Try**

1. In Part A, the inferred figure is a little below the truth. Read `simulate_conversation` and `signals` and work out which happy users are being missed.
2. In Part C, give one item a truly higher click rate. Which policy finds it?

## Write up in NOTES.md

Record the Part B table from lab 1, the threshold table from lab 2 with the embedding model's name, and all three parts of lab 3. Then answer: for a product you use, name two things users do that reveal whether an answer was good, and one way each could mislead.
