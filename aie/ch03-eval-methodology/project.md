## Goal

Compute the standard evaluation measures yourself on small examples, so that you know what each number can and cannot tell you.

Labs 1 and 3 are plain Python. Lab 2 uses an embedding model through Ollama (`nomic-embed-text`), so the Ollama app has to be running.

## Lab 1: perplexity

```bash
python lab1_perplexity.py
```

**What you should observe**

- Part A: a fair coin has 1 bit of entropy and a perplexity of 2. A coin that lands one way 90% of the time has under half a bit. Thirty-two equally likely tokens give 5 bits and a perplexity of 32.
- Part B: on new sentences from the language it learned, the model's perplexity is under 3. On the same sentences with the words shuffled it is in the thousands, far worse than the 31 a model that knew nothing would score.
- Part C: a sentence repeated 30 times in training scores a perplexity of about 2. Change one word and it more than triples.

**Try**

1. Remove the smoothing (set `k` to a much smaller value). What happens to the perplexity of shuffled text, and why?
2. Train on half as many sentences. Which of the three numbers in Part B moves the most?

## Lab 2: similarity to a reference

```bash
python lab2_similarity.py
```

One reference sentence and five candidates: identical, a paraphrase, one with a wrong day, a negation, and something unrelated.

**What you should observe**

- Exact match accepts only the identical sentence.
- Word overlap gives the paraphrase about 0.4, and gives the wrong-day and negated sentences about 0.9. It ranks the two wrong answers above the correct one.
- Embedding similarity gives the paraphrase about 0.8, which is far better. It still gives the wrong-day and negated sentences about 0.9.
- Only the unrelated sentence scores low on everything.

No threshold on any of the three columns separates the correct answers from the wrong ones. Your exact figures will vary a little with the embedding model.

**Try**

1. Add a sixth candidate that is correct but in another language. How do the three measures treat it?
2. Write a short judge prompt for a chat model that asks whether the candidate states the same facts as the reference, and try it on the negated sentence.

## Lab 3: comparative evaluation

```bash
python lab3_comparative_eval.py
```

Six models with hidden true skill play randomly paired matches. Ratings are fitted to the votes.

**What you should observe**

- Part A: with 30 or 300 votes the top two and the middle two are in the wrong order. From 3,000 votes the order is right.
- Part B: 100 models means 4,950 distinct pairs.
- Part C: a judge with a first-position preference, combined with a fixed order of presentation, stretches the gap between the best and worst model from about 375 points to nearly 700. Randomizing which answer is shown first brings it back to about the fair value.
- Part D: the top model beats the bottom one in 89% of comparisons, which says nothing about whether either is usable.

**Try**

1. Make C and D exactly equal in skill. How many votes does it take before their order stops flipping between runs?
2. Add a seventh model that only ever played ten matches. How far from its true skill does its rating land?

## Write up in NOTES.md

Record the Part B table from lab 1, the full table from lab 2, and Parts A and C from lab 3. Then answer: for an application you have in mind, which outputs could be checked exactly, and which would need a judge?
