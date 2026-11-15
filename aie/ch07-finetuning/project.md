## Goal

Do the arithmetic that decides whether a finetuning project is practical, and see quantization and low-rank adaptation working on something small enough to follow.

All three labs are plain Python with numpy and run in a few seconds.

## Lab 1: will it fit

```bash
python lab1_memory_math.py
```

**What you should observe**

- Part A: weights for a 7-billion-parameter model take 28 GB at 32 bits, 14 GB at 16 bits and 3.5 GB at 4 bits.
- Part B: with a 20% allowance for working memory, that model at 16 bits needs about 17 GB and does not fit a 16 GB device. At 4 bits it needs about 4 GB and fits everywhere. A 70-billion-parameter model at 4 bits fits only the largest device listed.
- Part C: fully finetuning the 7-billion model needs about 100 GB. Training 1% of its parameters needs under 18 GB, hardly more than inference.

**Try**

1. Add a row for a model you would like to run, on a device you have. Which format makes it fit?
2. In Part C, keep the weights in 4 bits while training a 0.1% adapter. What is the total now?

## Lab 2: quantization

```bash
python lab2_quantization.py
```

A small classifier with about 3,000 weights is trained, and its weights are then rounded to fewer and fewer distinct values.

**What you should observe**

- Accuracy is 93% at full precision and stays there at 16, 8, 6 and 4 bits, while the size falls from 11.5 kB to 1.4 kB.
- At 3 bits accuracy drops by about a point and a half, at 2 bits to about 88%, and at 1 bit to about 87%.

A model this small and a task this easy degrade gently. Large language models are more sensitive, which is why each quantized version is re-evaluated.

**Try**

1. Quantize only the first layer and leave the second at full precision, then the reverse. Which layer is more sensitive?
2. Clip the largest 1% of weights before quantizing. Does 2-bit accuracy improve?

## Lab 3: LoRA

```bash
python lab3_lora.py
```

One 64 by 64 layer stands in for a pretrained model. The new task needs a change to it that lies mostly along four directions.

**What you should observe**

- Full finetuning trains all 4,096 weights and removes the error entirely.
- LoRA with rank 1 trains 128 values and removes about 42% of the error; rank 2 about 67%.
- Rank 4 trains 512 values, 12% of the layer, and removes 99.9%. Ranks 8 and 16 add almost nothing.
- Folding the two small matrices into the layer gives identical outputs.
- At realistic sizes, a rank-8 adapter on a 4,096-wide layer is under half a percent of the layer.

**Try**

1. Change the task so that the needed change has rank 12. Which rank is now enough?
2. Initialize `B` with random values instead of zeros. What happens to the error at the very first step, and why does that matter?

## Write up in NOTES.md

Record the Part C table from lab 1, the table from lab 2, and the table from lab 3. Then answer: describe one problem you have seen that is a matter of facts, and one that is a matter of form.
