## Faster and cheaper

A model that gives excellent answers is of little use if each one takes thirty seconds or costs more than the feature earns. **Inference optimization** is the work of making a model respond faster and more cheaply without an unacceptable loss of quality.

It happens at three levels. You can change the model so that it needs less computation. You can choose and exploit hardware better. And you can organize the service around the model more cleverly. Even if you only ever call a provider's API, knowing these techniques explains the prices and latencies you see, and what you can do about them.

## Understanding inference

### Where the time goes

Producing a response has two phases with different characters.

In the first, sometimes called **prefill**, the model reads the input. All input tokens can be processed in parallel, so this phase is fast per token and is limited mainly by how much raw computation the hardware can do.

In the second, **decode**, the model writes the output one token at a time, each depending on those before. This cannot be parallelized in the same way, and it is limited mainly by how quickly data can be moved in and out of memory.

Those two limits have names. A workload is **compute-bound** when the calculation itself is the constraint, and **memory bandwidth-bound** when moving data is. Knowing which one applies tells you which optimization will help.

### Online and batch APIs

Providers typically offer two kinds of service. **Online** APIs answer as fast as possible, for products where someone is waiting, and can stream the answer token by token so the user sees progress. **Batch** APIs accept a large job and return it within hours, at a much lower price, because the provider can schedule the work for when capacity is free. Anything that does not need an immediate answer, such as scoring a backlog or generating training data, belongs on a batch API.

### Measuring performance

Latency is not one number.

- **Time to first token** is how long the user waits before anything appears. It is governed by the input: its length, and any queueing. It matters most for chat, where a quick first word makes the system feel responsive.
- **Time per output token** is how fast the rest arrives. For text a person reads, anything faster than reading speed adds little.
- **Total latency** is the first plus the second multiplied by the length of the output. It matters when the output is consumed whole, for example by another program.

Latency is a distribution, as chapter 2 of the first part of this course argued, so look at percentiles and not only the average.

**Throughput** is the number of tokens or requests the service handles per second, and it largely determines cost. Throughput and latency pull against each other: techniques that raise throughput often make individual requests slower.

**Goodput** corrects for that. It counts only the requests completed within your latency target. A service handling a hundred requests per second, half of them too slowly to be useful, has a goodput of fifty.

**Utilization** asks how much of the hardware's capability is actually being used. Expensive accelerators running at a small fraction of their potential are a common and costly finding.

## Hardware

Models run on **accelerators**, chips built for the highly parallel arithmetic that neural networks need. The dominant kind is the GPU. Three properties matter.

- **Computational power**: how many operations per second. This governs the compute-bound parts of the work.
- **Memory size and bandwidth**: whether the model and its working data fit at all, and how fast data moves. This governs the memory-bound parts, and memory size is often the first limit you hit.
- **Power consumption**: electricity and cooling are a large share of running costs and a real constraint on where data centres can be built.

Choosing hardware means matching these to the workload and budget. The most powerful chip is seldom the most economical one.

## Making the model faster

### Compression

The most direct approach is to make the model smaller. **Quantization**, from chapter 7, is the most widely used and usually the most effective: fewer bits per weight means less memory and less data to move. **Distillation** trains a smaller model to do the job of a larger one. **Pruning** removes weights that contribute little, and is used less in practice because the gains are harder to realize.

### The autoregressive bottleneck

Because output is produced one token at a time, each output token costs far more time than an input token. This is why providers charge more for output than for input, and it is the main target of several techniques.

**Speculative decoding** uses a small, fast model to draft several tokens ahead. The large model then checks the whole draft at once, which it can do in parallel, accepts the tokens it agrees with and takes over where it disagrees. When the draft is usually right, the output is the same as the large model's own, and arrives much faster.

A related trick applies when the output will mostly repeat the input, as when a model edits a document. Stretches of the input can be copied across and verified, instead of being regenerated token by token.

### Attention and the KV cache

When generating each new token, the model attends to all earlier tokens. Recomputing the internal representations of those earlier tokens at every step would be enormously wasteful, since they do not change. So they are computed once and kept in the **KV cache**, named after the keys and values of the attention mechanism. Every serious inference system does this.

The cache has to be stored, though, and it grows with the length of the context, the size of the model and the number of requests being processed together. For long contexts it can exceed the size of the model. It is often the thing that limits how many requests one accelerator can serve at a time. Lab 3 shows both the saving and the size.

### Kernels and compilers

The same model can run at very different speeds depending on how its operations are translated into instructions for a particular chip. Hardware vendors supply heavily tuned routines, and compilers can restructure a model for the target hardware, for instance by merging adjacent operations. This is specialist work that you mostly inherit by choosing a good inference framework.

## Making the service faster

### Batching

Processing several requests together uses the hardware far more efficiently than processing them one by one. There are three ways to form batches.

- **Static batching** waits until a fixed number of requests has arrived. It is simple, and when traffic is light the first request waits a long time for the batch to fill.
- **Dynamic batching** waits for a full batch or for a short time window, whichever comes first, so nobody waits more than the window.
- **Continuous batching** is designed for language models, where responses in a batch finish at different times. As soon as one response completes it is returned, and a new request takes its place, so short requests are not held up by long ones.

Batching raises throughput and lowers cost per request, and it adds some waiting. Lab 2 simulates the first two against serving one request at a time.

### Decoupling prefill and decode

Since reading the input and writing the output stress the hardware in different ways, they compete when run on the same machine. Assigning them to separate machines lets each be tuned for its job and improves both time to first token and output speed.

### Prompt caching

Many requests begin with the same text: a long system prompt, a document that users are asking about, or the earlier turns of a conversation. **Prompt caching** stores the result of processing that shared beginning, so later requests do not pay for it again. Providers that offer it charge much less for cached input tokens.

The saving can be large when the shared part is long and the unique part is short, and it is nothing when every request is different. It only works on a common beginning, so put the stable material first and the variable material last.

### Parallelism

The simplest way to serve more traffic is **replica parallelism**: run more copies of the model. A model too large for one chip can be split across several, which is model parallelism. Which combination is right depends on the size of the model, the hardware you have and whether you are optimizing for latency or for cost.

:::checkpoint[Users of a chat product say it "feels slow", although the total time for a full answer is reasonable. Which metric should you look at, and what might improve it?]
Time to first token. People judge responsiveness by how soon something appears. Streaming the output, shortening or caching a long shared prompt, and reducing time spent queueing all bring the first token forward without making the whole answer any faster.
:::

## What the labs show

- **Lab 1** streams responses from a model on your machine and measures time to first token and time per output token for three shapes of request.
- **Lab 2** simulates one accelerator under four loads with three batching policies, and reports goodput.
- **Lab 3** counts the work a KV cache saves, computes how large the cache gets, and works out what prompt caching saves in three scenarios.
