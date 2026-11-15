## From a model call to a system

The simplest AI application sends the user's request to a model and returns what comes back. Real products rarely stay that simple. This chapter builds up the usual architecture one component at a time, each added to solve a specific problem, then covers how to watch such a system and how to learn from the people who use it.

A warning first. Every component adds latency, cost and things that can break. Start with the simplest design that works and add a component when you can name the problem it solves.

## Building up the architecture

### Enhance the context

The first addition is usually giving the model the information it needs: retrieval from documents, search, and tools that fetch data. This was the subject of chapter 6. It does the most for quality and is where most systems begin.

### Add guardrails

Guardrails protect your users and your organization. There are two kinds.

**Input guardrails** check what goes into the model. One risk is sending private information to an outside provider: a user pastes in a customer's phone number, or retrieval pulls a confidential document. A common remedy is to detect sensitive values, replace them with placeholders before the request leaves, and put the real values back into the response afterwards. The other risk is the attacks described in chapter 5.

**Output guardrails** check what comes out. Failures are of two sorts. Quality failures: malformed output, a false statement, an answer that is simply poor. Security failures: toxic content, leaked private data, an instruction that would trigger a harmful action.

When a check fails, there are several possible responses. Retry, since the same request may well succeed the second time. Fall back to another model. Or pass the conversation to a person.

Guardrails cost time. Checks run before the model delay the start, and checks on the output delay the answer. Streaming makes output checks harder, because text has already been shown to the user before the whole response can be judged. Decide which risks justify the delay.

### Add a router and a gateway

Not every request needs your most capable model.

A **router** first works out what kind of request it is, usually with a small, fast classifier, and sends it to the appropriate place. Simple questions can go to a cheap model, hard ones to an expensive one, and requests outside the product's purpose can get a polite standard reply with no model call at all. Because simple requests are usually the majority, routing can cut costs sharply.

A **gateway** is a single layer through which all model calls pass, whichever provider serves them. It gives your code one consistent interface. It is where access control and spending limits are enforced, so that keys are not scattered through the organization. And it can provide a fallback: if one provider is failing or rate-limiting you, the gateway sends the request to another. Logging and caching fit naturally in the same layer.

### Add caches

Many requests repeat. A cache returns a stored answer without calling the model.

An **exact cache** returns a stored response only when the new request is identical to an earlier one. It is simple and safe, and it helps exactly as much as your traffic repeats.

A **semantic cache** returns a stored response when the new request is similar enough in meaning, judged by comparing embeddings. It catches rephrasings that an exact cache misses. It is also risky. Two questions can be close in wording and need different answers, and a cache hit then returns a confident answer to a question the user did not ask. The similarity threshold is hard to set, as lab 2 shows, and computing an embedding for each request has a cost.

With either kind, be careful what you store. A response that contains one user's information must never be served to another user. Caching only general answers, or keeping caches separate per user, avoids that.

### Add agent patterns

The last step lets the model take actions and work in loops, as chapter 6 described. This is the most powerful addition and the one that most increases the ways the system can fail, so it comes after the protections above are in place.

## Monitoring and observability

More components mean more ways to fail, and failures in AI systems are often quiet. The system keeps returning fluent answers that are worse than they were.

**Monitoring** means tracking known signals and raising an alert when they move. **Observability** is a property of the system: whether it records enough for you to work out what went wrong, including problems nobody anticipated, without deploying new code to find out.

A useful way to judge your setup is by three questions. How long does it take to detect that something is wrong? How long to fix it? And how often does a change cause a failure?

### What to track

- **Format failures**, such as output that does not parse.
- **Quality**, from the evaluation methods of chapter 3, run on a sample of real traffic.
- **Latency**, including time to first token and total time.
- **Cost and token usage**, per request and in total.
- **Guardrail activity**: how often each check fires.
- **User signals**, discussed below.

Break each of these down by user group, by version of the prompt and by model, so that a problem in one place is not averaged away.

### Logs and traces

Metrics tell you that something changed. **Logs** tell you what happened. Record everything needed to reconstruct a request: the full prompt as sent, the model and its settings, what was retrieved, each tool call and the final output. A **trace** links those records into the path one request took through the system, with the time and cost of each step, so that you can see where a bad answer or a slow response came from.

### Drift

Systems degrade without anyone touching the code. The system prompt gets edited. Users start asking for things they did not ask for before. And a provider may update the model behind an API without telling you. Each can change behaviour. Watching the measures above over time, and recording exactly which model version served each request, is how you notice.

## Orchestration

As components multiply, something has to connect them: take the request, call retrieval, build the prompt, call the model, check the result. Orchestration tools let you define components and chain them into pipelines, including steps that run in parallel or conditionally.

Two cautions apply. Do not adopt one at the start. Building the first version directly teaches you what your system needs, and an orchestrator can hide exactly what is being sent to the model. When you do choose one, check that it supports the components you use, that it can express your pipeline's shape, and that it does not add noticeable latency of its own.

## User feedback

### Why it matters

Feedback has always guided product development. In AI products it has a second role: it is data. What users ask and how they react is the raw material for evaluation and for improving the system, and it is something competitors do not have.

### Explicit and implicit feedback

**Explicit feedback** is what users give when asked: a thumbs up or down, a star rating. It is clear and it is rare, since most people never click.

**Implicit feedback** is inferred from what users do. It is abundant and noisy, and it needs interpretation.

### Reading conversations

A conversation is full of signals.

- **Early termination.** The user stops the response midway or leaves.
- **Error correction.** The user's next message starts with "no", restates the request, or says "I meant".
- **Regeneration.** Asking for another answer suggests the first was unsatisfactory, though sometimes the user only wants options.
- **Complaints and sentiment.** Explicit frustration or thanks.
- **Edits.** If the user changes the generated text before using it, the difference shows what was wrong.
- **Length of the conversation.** This one is ambiguous: a long exchange can mean an engaged user or one who cannot get an answer. It has to be read in the light of what the product is for.

### Designing feedback collection

Ask at moments when feedback is natural and worth having: when something goes wrong, and when the model is unsure, where offering two responses and asking which is better yields a useful comparison.

Make it effortless and easy to ignore. Feedback should never get in the way of the task. Tell users how it will be used, and respect their choices about their data.

### The limits of feedback

Feedback is biased, and treating it as ground truth leads you astray.

- **Leniency bias.** People rate more kindly than they feel, often to be polite or to get past a prompt. Satisfied ratings overstate satisfaction, and unhappy users tend to leave without rating at all.
- **Randomness.** Some clicks mean nothing.
- **Position bias.** People favour whatever is shown first. If you compare two responses, randomize the order.
- **Preference bias.** People may prefer the longer answer, or the one that agrees with them, over the correct one.

The deepest risk is a **degenerate feedback loop**: the system's output shapes the feedback, and the feedback shapes the system. Show people the most popular items and they become more popular because they were shown. Train on what users reward and a model can learn to flatter instead of to be right. Feedback should inform decisions together with other evidence, and never be optimized blindly.

:::checkpoint[After a redesign that shows the AI's answer above the human-written one, users pick the AI's answer more often. Does that show the AI's answers improved?]
No. Position alone makes people choose whatever is shown first, so the change in layout can explain the whole difference. To learn anything about quality, randomize which answer is on top and compare again.
:::

## What the labs show

- **Lab 1** masks personal data before a model call, then adds a router, a cache and a fallback to a simulated service and reports cost, latency and success rate.
- **Lab 2** uses a real embedding model to test a semantic cache on questions that mean the same and questions that only look alike.
- **Lab 3** reads satisfaction from logged behaviour, demonstrates position bias, and runs a feedback loop with and without exploration.
