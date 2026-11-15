## What changed

For most of its history, using machine learning in a product meant training a model. You collected data for one task, labelled it, trained a model for that task, and repeated the whole thing for the next task. It needed specialists and months.

That is no longer the usual starting point. A small number of very large models can now do a wide range of tasks out of the box, and you reach them through an API. Building a useful product has become mostly a matter of adapting one of these models and building a system around it. That activity is **AI engineering**, and this course is about doing it well. This first chapter explains where the models came from, what people build with them, how to decide whether to build something, and how the work is organized.

## From language models to foundation models

### What a language model does

A **language model** captures statistics about language: given some text, how likely is each possible continuation? Show it "the capital of France is" and it should give a high probability to "Paris".

There are two main styles. A **masked** language model fills in a blank using the text on both sides of it. An **autoregressive** language model predicts the next piece of text from what came before, and it is this style that generates text: predict one piece, append it to the input, predict again, and keep going.

Because the model outputs a probability for every possible continuation, and one is picked at random according to those probabilities, the same prompt can produce different answers. This makes models feel creative. It also makes them inconsistent, and it is why a model can state something false with complete fluency. Nothing is being looked up; a likely continuation is being produced.

It is worth noticing how much can be framed as "continue this text". Translation, summarizing, answering a question and writing code are all completions of a suitable prompt.

### Tokens

Models do not work with words or with characters. They work with **tokens**: a token can be a short word, a piece of a longer word, or a punctuation mark. The set of tokens a model knows is its vocabulary.

Tokens are a compromise. Characters would give a tiny vocabulary but extremely long sequences. Whole words would give short sequences but a vast vocabulary, and no way to handle a word the model has never seen. Pieces of words sit in between: common words are single tokens, and rare or new words are spelled out from familiar pieces.

Tokens matter to you in practice because limits and prices are counted in them. The amount of text a model can take in, the length of its answer and your bill are all measured in tokens, and the number of tokens per word differs between languages.

### Self-supervision

Classical machine learning needed labelled examples, and labelling is slow and expensive. Language models avoid it. Any piece of text provides its own training examples: hide the next token, ask the model to predict it, and compare with what was actually there. This is **self-supervision**. Since the internet contains an enormous amount of text, models could be trained on far more data than anyone could ever label, and that scale is what turned language models into *large* language models.

:::checkpoint[A model is trained only to predict the next token of text. Why can it translate from English to French?]
Its training text contained many examples of English followed by its French translation. Predicting the next token well in those contexts requires having learned the mapping. A translation request is then just a prompt whose most likely continuation is the translation.
:::

### Beyond text

The same approach was extended from text to images, audio and video, giving models that take more than one kind of input, known as multimodal models. The general term for all of them is **foundation model**: a large model trained on broad data that serves as a base for many applications. The break with the past is that one model is general purpose. You no longer need one model per task.

## Why this became an engineering discipline

Three things came together. The models became capable enough to be useful across a huge range of tasks. Companies invested heavily in building on them. And the barrier to entry collapsed: training such a model is out of reach for almost everyone, but using one takes an API call and a description of what you want in plain language.

So demand for applications rose while the skill needed to build a first version fell. That is why so many people are now building with AI, and why a good demo has become easy to produce.

## What people build

Applications fall into a handful of recurring groups:

- **Coding**: completing, writing, explaining and translating code.
- **Image and video production**: generating and editing visual material.
- **Writing**: drafting, rewriting and proofreading, from emails to reports.
- **Education**: tutoring, practice questions, feedback on work.
- **Conversational bots**: customer support, assistants, companions.
- **Information aggregation**: summarizing documents, meetings and search results.
- **Data organization**: extracting structure from documents, images and messages.
- **Workflow automation**: carrying out multi-step tasks, often by calling other tools.

The tasks most exposed to automation are those that are mostly reading and writing with clear success criteria. In companies, internal tools tend to be deployed before customer-facing ones, because mistakes are cheaper there.

## Planning an AI application

### Should you build it

Being able to build something is not a reason to build it. Start with why. Is it a threat, where a competitor using AI could make your product obsolete? Is it an opportunity to raise revenue or lower costs? Or are you exploring so as not to be left behind? The answer sets how much risk is reasonable.

Then look at the role AI plays in the product:

- **Critical or complementary.** If the product cannot work without the AI, the AI has to be very good. If it is an optional extra, there is more room for error.
- **Reactive or proactive.** A feature that responds to a request must be fast. One that acts on its own initiative can take its time, but it had better be right, since nobody asked for it.
- **The role of people.** Will a person review the output before it is used, or does the model act directly? Many products start with a human in the loop and remove it as trust builds.

Finally, ask what makes the product hard to copy. If it is a thin layer over someone else's model, the model's provider or a competitor can reproduce it quickly. Lasting advantages tend to come from proprietary data, from distribution, or from being embedded in how customers already work.

### Setting expectations

Decide in advance how you will know the product works. That means business measures, such as tickets resolved or time saved, and technical ones: quality of output, latency, and cost per request. Agree on a threshold of usefulness, the point at which the product is good enough to put in front of people.

### The last mile

A working demo can take a weekend. A dependable product can take a year. Early progress is fast and it is tempting to extrapolate from it, but each further step in reliability is harder than the last: handling unusual inputs, cutting down false statements, keeping latency and cost under control. Plan milestones that take this into account, and do not promise a date from how the demo went.

### Maintenance

The ground moves under an AI product. Models improve and get cheaper month by month, so a decision made on today's prices and limits may be wrong in a year. A provider may change or retire the model you depend on. Regulation is evolving. Design so that the model can be swapped, and re-examine build-or-buy decisions regularly.

## The AI engineering stack

### Three layers

- **Application development.** Give a model good instructions and the right context, and build the interface around it. The core activities are evaluation, prompt engineering and designing the AI interface. Most of the work now happens here.
- **Model development.** Change the model itself: finetuning, preparing datasets, and making inference faster and cheaper.
- **Infrastructure.** Serve models, manage compute and data, and monitor everything.

### How it differs from ML engineering

AI engineering grew out of machine learning engineering, and many principles carry over. The emphasis is different in four ways.

- **Adapting, not training.** You start from a model someone else trained. Deep training expertise matters less; knowing how to steer and assess a model matters more.
- **Bigger models.** They are expensive and slow to run, so making inference efficient is a central concern.
- **Open-ended outputs.** A classifier picks from a fixed list, so checking it is easy. A foundation model can say anything, which makes evaluation far harder and far more important.
- **A reversed workflow.** Traditional ML started with data, then a model, then a product. Now you can start with a product built on an existing model, and invest in data and custom models only if the product proves its worth.

That last point also explains why people from web and application development have moved into the field: the first version of an AI product is mostly product engineering.

## What the labs show

- **Lab 1** builds a language model from nothing but counts, and uses it to show self-supervision, next-token probabilities, generation and filling a blank.
- **Lab 2** trains a small subword tokenizer and shows how the vocabulary size changes the way words are split.
- **Lab 3** calls a real model running on your machine and measures sampling behaviour and token counts.
