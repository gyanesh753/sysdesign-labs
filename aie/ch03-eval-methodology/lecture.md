## Why evaluation is the hard part

With a traditional classifier, evaluation is simple: compare the predicted label with the correct one and count. A foundation model can answer in an unlimited number of ways, many of them acceptable and many subtly wrong. There is rarely a single right answer to compare against.

Several things make it harder still. The more capable a model is, the more expertise it takes to judge its work; checking a proof needs a mathematician. Most models are available only through an API, so you cannot see how they were trained or on what. Public benchmarks are quickly outgrown. And evaluation gets far less attention than building, so the tooling lags.

Yet evaluation is what separates a product from a demo. Without it you cannot tell whether a change helped, and you find out about failures from your users. This chapter covers the methods. The next applies them to a real system.

## Language modelling metrics

These measure how well a model predicts text. They tell you about the underlying model, not directly about your application, but they come up constantly and are worth being able to read.

### Entropy and cross entropy

**Entropy** measures how much information each token carries on average, which is the same as how unpredictable the text is. A source that always produces the same token has an entropy of zero. One that picks uniformly among many tokens has a high entropy.

**Cross entropy** measures how well a particular model predicts a particular body of text. It is low when the model gives high probability to what actually comes next. Training a language model amounts to lowering its cross entropy on the training data.

### Perplexity

**Perplexity** is the same quantity on a friendlier scale. Loosely, it is the number of options the model is hesitating between at each step. A perplexity of 3 means the model is, on average, as unsure as if it were choosing among three equally likely tokens. Lower is better.

A few rules of thumb help when reading it:

- More structured text has lower perplexity. Code and markup are more predictable than free prose.
- A bigger vocabulary gives higher perplexity, so numbers from models with different tokenizers are not directly comparable.
- More context gives lower perplexity, since the model has more to go on.

Perplexity has practical uses beyond training. Text the model has seen before tends to have unusually low perplexity, which gives a way to test whether a benchmark or a private document was in the training data. Text with unusually high perplexity is likely to be gibberish or out of the ordinary, which is useful for filtering data.

## Exact evaluation

Some methods give a definite answer with no judgment involved. Use them wherever they apply.

### Functional correctness

The best test of an output is whether it does the job. For generated code, run it against test cases. For a query, execute it and compare the result. For an agent booking a meeting, check the calendar. Not every task can be checked this way, but where it can, nothing else is as trustworthy.

### Similarity to reference data

Where function cannot be tested directly, you can compare the output with one or more **reference** answers known to be good. The quality of the evaluation then depends on the quality and coverage of the references, and producing them is the expensive part.

There are three ways to compare.

- **Exact match.** The output must equal a reference. This suits short answers such as a number or a name, and fails for anything longer, since a correct answer can be worded in many ways.
- **Lexical similarity.** Count the overlap in words or word sequences between output and reference. It is cheap and easy to understand. It also rewards answers that share words with the reference while being wrong, and penalizes correct answers that use different words.
- **Semantic similarity.** Compare meanings by turning both texts into embeddings and measuring how close they are.

### Embeddings

An **embedding** is a list of numbers that represents a piece of data. A good embedding model places things with similar meanings close together and unrelated things far apart, and closeness is usually measured by cosine similarity. Embeddings are behind search, clustering, deduplication and recommendation as well as evaluation, and they exist for images and audio as well as text, including models that place text and images in the same space.

Semantic similarity is only as good as the embedding model, and it has blind spots. Lab 2 shows one: a sentence and its negation, which mean opposite things, come out as nearly identical.

## AI as a judge

### Why use a model to judge

Since models can assess text, a natural step is to have one evaluate another's output. It is fast and cheap compared with human reviewers, it needs no reference answer, it can apply almost any criterion you can describe, and it can explain its verdict. In many studies its judgments agree with human ones reasonably well. This has made it the most common way to evaluate applications in production.

### How to set it up

A judge is a model plus a prompt. There are three basic forms:

- Assess a response on its own against stated criteria: is this answer polite, is it relevant to the question?
- Compare a response with a reference: does it say the same thing as the expected answer?
- Compare two responses and say which is better.

The prompt should state the task, the criteria and the scoring system. Judges are more reliable with a small number of discrete options, such as yes or no, or a scale of one to five, than with fine-grained numeric scores. Including a few examples with their correct scores helps a great deal.

### Limitations

A judge is itself a model, with every weakness that implies.

- **Inconsistency.** The same judge can score the same input differently on different runs. Low temperature and examples reduce this.
- **Ambiguous criteria.** Words like "faithful" or "relevant" are defined differently by different tools. A score is meaningless without the prompt that produced it, and scores from different judges cannot be compared.
- **Drift.** If the judge's model or prompt changes, scores change even though your application did not. Treat the judge as part of your system and version it.
- **Cost and latency.** Judging every response can double your spending. Judging a sample is usually enough.
- **Bias.** Judges tend to favour responses generated by the same model, the response shown first in a comparison, and longer responses regardless of quality.

A judge does not need to be the strongest model available. A smaller model can be good enough for a narrow criterion, and specialized small judges exist for particular jobs.

:::checkpoint[Your quality score dropped by ten points overnight, but you deployed nothing. What should you check first?]
Whether anything about the judge changed: the model behind it, its prompt, or its sampling settings. A score is produced by the judge as much as by the application, so an update on the judge's side moves the number without any change in real quality.
:::

## Ranking models by comparison

### How it works

Instead of scoring each model separately, **comparative evaluation** has models compete. Two models answer the same prompt, a person or a judge picks the better answer, and after many such matches a rating algorithm turns the results into a ranking. People find it easier to say which of two answers is better than to put a number on one.

### What it cannot tell you

- **It scales poorly.** The number of possible pairs grows with the square of the number of models, and each new model has to be compared with many others.
- **Quality control is difficult.** With public voting, anyone can vote on any prompt. Simple prompts dominate, voters may not be qualified to judge specialized answers, and the prompts may be nothing like your use case.
- **It is relative.** A ranking tells you that one model is preferred to another. It does not tell you whether either is good enough for your purpose, or by how much the better one is worth its extra cost.

A public leaderboard is a reasonable place to start a shortlist. It is not a substitute for testing on your own data.

## What the labs show

- **Lab 1** computes entropy for simple cases, then the perplexity of a tiny model on predictable, scrambled and memorized text.
- **Lab 2** scores five candidate answers against one reference using exact match, word overlap and a real embedding model.
- **Lab 3** recovers a ranking of six models from simulated votes, and shows what a judge with a first-position bias does to it.
