## Goal

Work through the arithmetic behind three things you will adjust or reason about constantly: sampling settings, model size, and spending extra computation per request.

All three labs are plain Python with numpy and run in a second or two.

## Lab 1: sampling

```bash
python lab1_sampling.py
```

The script starts from ten made-up logits for the token that follows "My favourite colour is".

**What you should observe**

- Part A: softmax gives "blue" 43%, "green" 24%, "red" 18%, and small amounts to the rest.
- Part B: at temperature 0.2 "blue" gets 94% and only four distinct tokens appear in 1,000 samples. At 3.0 it gets 21%, every token appears, and nonsense tokens are picked about 9% of the time.
- Part C: top-k with k of 3 leaves only blue, green and red, with their probabilities rescaled.
- Part D: top-p of 0.9 keeps a single token for a confident model and eight for an unsure one.
- Part E: "blue" has a log probability of about minus 0.8 and "banana" about minus 5.8.

**Try**

1. Combine a temperature of 1.5 with top-p of 0.9. Does the nonsense rate drop while variety stays?
2. Compute the log probability of a three-token answer where each token has probability 0.5. Why are logs added?

## Lab 2: attention and size

```bash
python lab2_attention.py
```

**What you should observe**

- Part A: a table of attention weights for a five-token sentence. Each row adds up to one, and everything above the diagonal is zero because a token cannot look ahead.
- Part B: the number of token pairs grows with the square of the context: a million for 1,000 tokens, over 16 billion for 128,000.
- Part C: a model with 32 layers of width 4,096 has about 5 billion parameters in this simplified count, needing about 21 GB at 32 bits per parameter and under 3 GB at 4 bits.

The vectors in Part A are random, so the weights carry no meaning. In a trained model they are learned.

**Try**

1. Remove the causal mask. What changes in the weight table, and why would that be cheating during training?
2. Double the width of the medium model while keeping the layers. By what factor do the parameters grow?

## Lab 3: test-time compute

```bash
python lab3_test_time_compute.py
```

**What you should observe**

- Part A: a model that is right 60% of the time, with scattered wrong answers, reaches about 84% with five samples and over 96% with eleven.
- Part B: a model that prefers one particular wrong answer does not improve, and with 25 samples it is worse than with one.
- Part C: if each candidate passes a test 30% of the time, ten candidates give a 97% chance that at least one passes.

**Try**

1. In Part A, what is the smallest number of samples that reaches 90%? What does that cost compared with a model that is right 90% of the time at three times the price?
2. In Part C, make the checker unreliable: it accepts a wrong candidate 5% of the time. How does the benefit change?

## Write up in NOTES.md

Record the Part B table from lab 1, the Part C table from lab 2, and all three tables from lab 3. Then answer: for a task you care about, would you set the temperature low or high, and is there a way to check an answer automatically?
