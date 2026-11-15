## From methods to decisions

The previous chapter described ways to score a model's output. This one is about using them: deciding what matters for your application, choosing a model, and building a process that tells you reliably whether the system is good enough.

A habit worth adopting from the start is **evaluation-driven development**. Before building anything, write down how you will know it works. It is the same idea as writing a test before the code. Teams that skip this tend to ship things that demo well and that nobody can prove are improving.

## Evaluation criteria

What "good" means depends on the application, but most criteria fall into four groups.

### Domain-specific capability

Does the model have the knowledge and skill the task needs? A model that cannot write SQL will not become a good data assistant however you prompt it. This is usually tested with benchmarks for the field, often made of questions with definite answers such as multiple choice, which can be scored exactly.

### Generation capability

Early text generators were judged on whether their output read fluently and hung together. Current models nearly always pass those tests, so attention has moved to harder properties.

The most important is **factual consistency**. It comes in two forms:

- **Local**: is the output consistent with the context it was given? A summary should not contradict the document it summarizes.
- **Global**: is the output consistent with what is known about the world?

Local consistency is easier to check, because the evidence is right there. Global consistency requires finding reliable evidence first, which is hard in itself.

Ways of checking include a model judge that is given the source and the output, comparing several responses to the same question on the assumption that a model which contradicts itself is probably making things up, and searching for evidence and then checking each claim against it.

Safety is the other major property in this group: whether the output is toxic, biased, or otherwise harmful. Dedicated classifiers exist for this.

### Instruction-following capability

Can the model do what it is told? If you ask for JSON, a rating from one to five, or an answer of at most three sentences, you need exactly that, because code downstream depends on it. A model can be knowledgeable and still poor at respecting constraints. Tests here check formats and stated limits. Staying in an assigned role or persona throughout a conversation is a related skill, important for assistants and games.

### Cost and latency

A model that is excellent, slow and expensive may be useless for your purpose. Latency has several parts: how long until the first token appears, how fast tokens arrive after that, and the total time. Cost is usually counted per token for an API, or as hardware and engineering time if you host the model.

These pull against quality, so decide which requirements are firm limits and which are preferences before comparing models.

## Model selection

### The workflow

Choosing a model is a process of elimination that you repeat as things change.

1. Remove models that fail your hard requirements: licence, privacy rules, hardware, a maximum latency.
2. Use public information, such as benchmarks and leaderboards, to narrow the rest to a shortlist.
3. Run your own evaluation on the shortlist with your own data, balancing quality, latency and cost.
4. Keep monitoring the chosen model in production, and revisit the choice when new models appear.

It helps to separate attributes you cannot change from those you can. A licence or a provider's privacy policy is fixed. Accuracy or latency can often be improved with better prompts, more context or optimization.

### Use an API or host it yourself

For most teams the real question is whether to call a commercial model through an API or run an open model on their own infrastructure. The considerations:

- **Data privacy.** Sending data to an outside provider may be forbidden by your policies or by law.
- **Data lineage and copyright.** You may need to know what a model was trained on, and who owns its output.
- **Performance.** The strongest models have tended to be proprietary, though the gap moves.
- **Functionality.** An API may not expose things you need, such as log probabilities or finetuning. A hosted model gives you everything, and makes you build the scaling and safeguards yourself.
- **Control.** A provider can change the model, impose rate limits, or shut it down. With your own copy, nothing changes unless you change it.
- **Cost.** APIs charge per use, which is cheap at low volume. Hosting has a high fixed cost in hardware and people, and becomes economical only at scale. Lab 2 works through the arithmetic.
- **On-device use.** If the model must run without a network connection, hosting is the only option.

Check licences carefully. "Open" covers a wide range: some models publish their weights but restrict commercial use, and few publish their training data.

### Reading public benchmarks

There are thousands of benchmarks, and a leaderboard combines a handful into a ranking. Read them with some care.

- The choice of which benchmarks to include, and how to weight them, is largely arbitrary. A different selection gives a different order.
- Benchmarks saturate. Once most models score near the top, the benchmark no longer separates them.
- The benchmarks may have nothing to do with your task. It is better to assemble a private leaderboard from the benchmarks that reflect what you need.

The most serious problem is **data contamination**: the model was trained on the very questions it is being tested on. This usually happens by accident. Benchmarks are published, the web is scraped for training data, and the test ends up in the training set. The score then measures memory, not ability.

You can look for contamination by checking whether long word sequences from the benchmark appear in the training data, when you have access to it, or by checking whether the model finds the benchmark text suspiciously predictable. Benchmark authors defend against it by keeping part of the data private. When you can identify which examples a model has seen, report its score on the rest.

:::checkpoint[A new model tops a coding leaderboard, but performs no better than your current model on your own tasks. Give two plausible explanations.]
The benchmark problems may have been in its training data, so the score reflects memorization. Or the benchmark may simply measure something different from your tasks: other languages, other kinds of problem, short puzzles instead of work on a large existing codebase.
:::

## Designing an evaluation pipeline

### Evaluate every component

An application is usually several steps: retrieve documents, write a query, generate an answer. Evaluate the final result, and also each step separately. When the final answer is wrong, you need to know which step failed.

For conversational applications, distinguish judging a single turn from judging the whole task. What matters to the user is whether their problem was solved, and in how many turns.

### Write the guideline

Often the hardest part is deciding what a good response is. A correct answer may still be a bad one if it is unhelpful or off-topic. Write it down:

- **Criteria.** State what the application should and should not do.
- **A scoring rubric with examples.** For each criterion, define the scale and show examples of each score. If people cannot apply the rubric consistently, a model will not either.
- **A link to business outcomes.** Connect each metric to something the business cares about, for instance what level of factual consistency is needed before a given share of support requests can be handled automatically. This tells you what score is good enough, and what improving it is worth.

### Choose methods and data

Combine methods according to cost. A cheap check can run on every response, a model judge on a sample, and human review on a smaller sample that also keeps the judge honest.

Build a set of test examples that represent real usage, and pay attention to how you divide it.

- **Slice the data.** Look at results for separate groups: by type of user, by topic, by input length. An average can hide a serious failure on one group. It can even reverse the picture: one system can be better on every slice and worse overall, purely because the slices were mixed in different proportions. Lab 1 shows a case.
- **Use enough examples.** A small test set gives a noisy score, and a difference of a few points may be luck. Resampling your test set many times and looking at how much the score varies tells you how far to trust it. The smaller the improvement you want to detect, the more examples you need.

Finally, check the pipeline itself. Does it give the same result when run twice? Do better scores correspond to better outcomes? What does it cost to run? An evaluation nobody trusts will not be used.

## What the labs show

- **Lab 1** shows a system that wins on every slice and loses on the average, then measures how large a test set must be to detect a three-point difference.
- **Lab 2** walks a set of candidate models through hard requirements, trade-offs and a break-even calculation between an API and self-hosting.
- **Lab 3** builds a model that understands nothing, lets 60% of a benchmark leak into its training data, and detects the contamination.
