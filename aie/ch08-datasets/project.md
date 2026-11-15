## Goal

Handle a dataset the way you would before training on it: find the copies, see what cleaner data is worth, and generate and verify more.

All three labs are plain Python with numpy and run in a few seconds.

## Lab 1: duplicates

```bash
python lab1_dedup.py
```

2,000 generated instructions, plus 450 planted copies: 150 exact, 150 differing only in casing and spacing, and 150 with a word replaced.

**What you should observe**

- Exact hashing finds 150 of the 450. Hashing after normalizing case and spacing finds 300. Neither removes anything it should not.
- Similarity search with a strict threshold of 0.95 finds the same 300.
- At 0.75 it finds a few more, and wrongly removes over 200 originals.
- At 0.6 it finds 425 of the 450, and wrongly removes more than 1,600 originals, most of the dataset.
- MinHash signatures cut 3 million possible comparisons to under half a million.

These examples come from templates, so many genuinely different instructions share most of their words. That is exactly the situation in which a loose threshold does damage.

**Try**

1. Compare on three-word sequences instead of two. Does that separate reworded copies from legitimately similar examples better?
2. Find the threshold that maximizes copies found minus originals wrongly removed.

## Lab 2: quantity and quality

```bash
python lab2_quality_vs_quantity.py
```

**What you should observe**

- Part A: accuracy rises from about 70% with 50 examples to about 85% with 1,600, and then barely moves. The last two doublings add well under a point each.
- Part B: 500 correctly labelled examples give about 83% on class 0. With 5,000 examples in which 60% of class 0 is mislabelled, accuracy on that class falls to about 34%. With 50,000 such examples it is the same.

Random noise tends to average out with more data. A consistent mistake does not: the model learns it.

**Try**

1. Change the corruption so that mislabelled examples go to a random class instead of always to class 1. Does more data help now?
2. Fix the labels on only 500 of the 5,000 corrupted examples. How much does accuracy on class 0 recover?

## Lab 3: synthesis

```bash
python lab3_synthesis.py
```

**What you should observe**

- Part A: three hand-written examples become 1,248 through four phrasings, three operations and a range of numbers.
- Part B: a generator that is wrong about 8% of the time produces about a hundred wrong answers. Recomputing each answer rejects all of them.
- Part C: when each generation is trained only on the previous one's output, the spread of the data falls from 1.02 to 0.47 over eight generations, and the share of rare cases falls from 5% to zero by the fourth.

**Try**

1. In Part C, mix 20% real data into each generation. Does the spread still shrink?
2. In Part B, replace the exact check with a judge that is itself wrong 5% of the time. How many bad examples get through, and how many good ones are thrown away?

## Write up in NOTES.md

Record the table from lab 1, both tables from lab 2, and Parts B and C from lab 3. Then answer: for a task you might finetune on, where would the first hundred good examples come from, and who would write the guideline?
