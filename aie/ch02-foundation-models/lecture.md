## Why look inside

You do not need to know how to train a foundation model to build with one. But many of a model's odd behaviours stop being mysterious once you know four things about how it came to be: the data it learned from, its architecture and size, the tuning it received after pre-training, and how its output is sampled. Those four also decide which model suits your task and how to get the most from it.

## Training data

A model can only be as good as the data it was trained on. If a kind of text was rare or missing, the model will be weak at it, however capable it looks elsewhere.

Most large models learn from text gathered from the web. That makes them broad, and it also means they absorb whatever the web contains: misinformation, low-quality writing and bias.

Two consequences matter in practice.

**Language.** English dominates the web, so models are at their best in English. Languages with little text online are called low-resource, and models perform noticeably worse in them. They are also more expensive to use, because the same meaning takes more tokens. Translating to English and back is a workaround, but it loses nuance.

**Domain.** A general model does well on topics that are common on the web and poorly on specialized material that is rare, proprietary or in an unusual format, such as medical scans or protein sequences. Domain-specific models are trained on carefully curated data for those fields.

More data is not automatically better. A smaller amount of high-quality, relevant data often beats a larger pile of noise.

## Architecture and size

### The transformer and attention

Nearly all current language models use the **transformer** architecture. Its predecessors read text one token at a time and squeezed everything read so far into a single running summary, so details from early in a long input were easily lost.

The transformer's central idea is **attention**. When producing a token, the model can look directly at every earlier token and weigh how relevant each one is. Each token offers a key describing what it contains, the current position forms a query describing what it needs, and the match between query and key sets how much of that token's content is used. Lab 2 computes this by hand.

A transformer is a stack of identical blocks, each containing an attention module and a small feedforward network. Before the stack, tokens are converted into vectors. After it, an output layer turns the final vector into a score for every token in the vocabulary.

Because the input can be processed in parallel, transformers train efficiently on modern hardware. Generation is still one token at a time, which is why long outputs are slow.

### Three numbers for size

- **Parameters.** The number of values the model learned. More parameters mean more capacity to learn, and more memory and compute to run.
- **Training tokens.** How much text the model learned from.
- **Training compute.** The total amount of calculation spent on training.

A fourth number matters when you use the model: the **context length**, the maximum number of tokens it can take in at once.

Bigger is not always the right choice. A larger model needs correspondingly more data to be worth its size, costs more per request and responds more slowly. For many tasks a smaller model is enough.

## Post-training

A model that has only been pre-trained is good at continuing text. That is not the same as being a good assistant. Ask it a question and it might answer, or continue with another question, or wander off. It will also happily produce harmful or useless text, because such text exists in its training data. Two further stages fix this.

### Supervised finetuning

The model is shown many high-quality examples of prompts with appropriate responses, written by skilled people. From these it learns to treat its input as a request to be answered, in the format expected. The examples are expensive to produce, because writing a good response often takes real expertise.

### Preference finetuning

The second stage teaches the model which responses people prefer: helpful, honest, and safe. A common method collects comparisons, where people are shown two responses to the same prompt and choose the better one. A separate reward model is trained to predict those choices, and the main model is then tuned to produce responses the reward model scores highly. Simpler methods that learn from the comparisons directly are increasingly used.

Preferences are not universal. People disagree about what a model should say on contested subjects, and whichever choices a provider makes will not suit everyone.

## Sampling

### From scores to probabilities

For each position the model produces a raw score, called a **logit**, for every token in its vocabulary. A function called softmax converts those scores to probabilities that add up to one. The next token is then drawn at random according to those probabilities. Always taking the single most likely token sounds safer, but it tends to give repetitive, dull text.

Providers often expose **log probabilities** for the tokens produced. They are useful for judging how confident a model was, and for classification tasks.

### Temperature, top-k and top-p

Three controls shape the randomness.

- **Temperature** rescales the logits before softmax. A low temperature sharpens the distribution so the likeliest tokens dominate, giving predictable output. A high temperature flattens it, giving more varied output and more chance of nonsense. A temperature of zero means always taking the most likely token.
- **Top-k** considers only the k highest-scoring tokens.
- **Top-p** considers the smallest set of tokens whose probabilities add up to p. Unlike top-k, the size of that set adapts: a single token when the model is confident, many when it is unsure.

For tasks with one right answer, such as extraction, use a low temperature. For brainstorming or creative writing, raise it.

### Stopping

A model keeps generating until it produces a special end token, hits a limit on output tokens, or produces a stop sequence you specified. A limit that is too low cuts the answer off mid-sentence, which is a common cause of malformed output.

### Test time compute

Instead of one response, you can generate several and choose among them. You might pick the one with the highest average log probability, the answer that appears most often, or the one that passes a check such as a test suite. This spends more computation per request to get a better result, and it works best when there is a reliable way to tell a good answer from a bad one. Lab 3 shows both when it helps and when it backfires.

### Structured outputs

Applications often need output in an exact format such as JSON. There are four approaches, in rising order of effort and reliability: ask for the format in the prompt, with examples; repair small errors afterwards in code; constrain sampling so that only tokens that keep the output valid can be chosen; or finetune the model on the format.

## The consequences of sampling

### Inconsistency

Because output is sampled, the same input can give different outputs, and a slightly different input can give a very different one. Users find this confusing. You can reduce it by caching answers so a repeated question gets the same reply, by lowering the temperature, and by fixing the random seed where the provider allows it. None of these guarantees consistency across model versions or hardware.

### Hallucination

A model sometimes produces statements that are fluent, confident and false. This follows from what it is: a system that produces likely text, not one that retrieves facts.

Two explanations are commonly given. One is that a model cannot tell what it was given from what it generated itself, so once it has produced a false statement it carries on as though the statement were established. The other is that training taught it to answer in the manner of someone who knows, including on matters where the model lacks the knowledge.

There is no complete cure. Supplying the relevant facts in the prompt, asking for short answers, asking the model to say when it does not know, and checking output against sources all help.

:::checkpoint[Your support bot gives two customers different answers to the same billing question. Which settings and techniques would you look at first?]
The temperature, which should be low for factual answers; whether answers to common questions are cached; and whether the two prompts were really identical, since small differences in wording or retrieved context can change the output. Then consider whether the answer should come from a looked-up source instead of the model's memory.
:::

## What the labs show

- **Lab 1** turns a set of logits into probabilities and applies temperature, top-k and top-p to them.
- **Lab 2** computes self-attention for a five-token sentence and counts the parameters and memory of models of three sizes.
- **Lab 3** simulates generating several answers and voting or checking, including a case where voting makes things worse.
