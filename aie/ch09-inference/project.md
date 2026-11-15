## Goal

Measure the latency numbers that matter on a real model, then explore two service-level trade-offs with simulations you can change.

Lab 1 calls a chat model through Ollama. Labs 2 and 3 are plain Python. The prices in lab 3 are invented.

## Lab 1: latency on a real model

```bash
python lab1_latency_metrics.py
```

Four requests are streamed, and the arrival time of each piece of the answer is recorded. The long prompt contains a random number, so it is new to the server on every run.

**What you should observe**

On my machine, with one particular model:

- A short prompt with a one-word answer: first token after about 0.1 to 0.2 seconds, and that is the whole response.
- A short prompt with a 200-token answer: the first token is just as quick, each further token takes about 30 ms, and the total is over 6 seconds.
- A prompt of about a thousand tokens, seen for the first time: the first token takes roughly a second, several times longer than for the short prompt.
- The same long prompt sent again: the first token arrives almost as fast as for the short prompt. The server reused its processing of the prompt.

Your timings will differ. The pattern should not: input length moves the first token, output length moves the total, and a repeated beginning is nearly free.

**Try**

1. Change only the last sentence of the long prompt and send it again. Is it still fast? Then change the first sentence instead. What does that tell you about what a cache can reuse?
2. Compute how many words per second the model writes. How does that compare with how fast you read?

## Lab 2: batching

```bash
python lab2_batching.py
```

One accelerator. A single request takes 72 ms and a batch of sixteen takes 252 ms. A response slower than 400 ms counts as a failure.

**What you should observe**

- At 5 requests a second, serving one at a time is fastest and everything is in time. Fixed batches of sixteen are disastrous: the median wait is over a second and a half, because the batch takes seconds to fill.
- At 12 a second, one at a time is already missing the limit for a fifth of requests. Dynamic batching serves all of them in time.
- At 40 a second, one at a time has collapsed completely, with waits of minutes. Dynamic batching still serves everything in time.
- At 60 a second even dynamic batching gets only about 58% within the limit. The machine is simply full.

**Try**

1. Change the dynamic window from 30 ms to 5 ms and to 150 ms. What happens at light load and at heavy load?
2. Find the highest load at which dynamic batching keeps 99% of requests within the limit. That is this machine's real capacity.

## Lab 3: caches

```bash
python lab3_kv_cache.py
```

**What you should observe**

- Part A: generating 1,000 tokens after a 500-token prompt involves over a billion token pairs without a cache and about 1.25 million with one, a saving of several hundred times.
- Part B: for a model with 32 layers of width 4,096, the cache for one 32,000-token context is about 17 GB. For a batch of sixteen such contexts it is about 270 GB.
- Part C: a support bot whose 4,000-token system prompt is shared by every request saves about 84% of its input cost with caching. Requests with nothing in common save nothing.

**Try**

1. In Part C, move the shared text to the end of each prompt instead of the beginning. What should the saving be, and why?
2. In Part B, halve the bytes per value. Which chapter 7 technique does that correspond to?

## Write up in NOTES.md

Record the table from lab 1 with your model's name, the 12 and 40 requests-per-second rows from lab 2, and Part C from lab 3. Then answer: for a product you have in mind, which matters more, time to first token or total latency, and why?
