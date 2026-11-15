## Data sets the ceiling

There are two ways to make a model better at a task. You can improve the model: a new architecture, a bigger size, a different training method. Or you can improve the data it learns from. When everyone has access to the same strong base models, the model is not what separates one team from another. The data is.

**Dataset engineering** is the work of creating a dataset that lets you train the best model you can within your budget. It is unglamorous and it decides the outcome more often than any choice of technique. It has three parts: curating what you need, generating what you lack, and processing all of it into usable shape.

## Data curation

Deciding what data to collect begins with what you want the model to do. To teach step-by-step reasoning, the examples must contain the reasoning, not only the final answers. To teach the use of tools, they must show tools being called. To teach conversation, they must be conversations. A dataset can only teach what it demonstrates.

Three properties then decide how good it is.

### Quality

A small amount of good data beats a large amount of poor data. Good examples are:

- **Relevant** to the task you actually have.
- **Aligned with what the task requires.** If answers must be factually right, the examples must be right. If they must be concise, the examples must be concise.
- **Consistent.** Two annotators given the same input should produce the same label. If they disagree, the model is being taught two contradictory things.
- **Correctly formatted**, with no stray markup or truncated text.
- **Sufficiently unique**, without piles of duplicates.
- **Compliant** with the law and your own policies, for instance free of personal data you have no right to use.

### Coverage

The data should span the range of situations the model will meet. If users write short and long requests, formally and casually, with and without typing mistakes, on many topics, the training data should include all of that in sensible proportions. A model trained only on tidy examples struggles with messy real input.

### Quantity

How much is enough depends on several things. Training every parameter needs more data than training a small adapter. A complex task needs more than a simple one. A strong base model needs less than a weak one.

A practical approach is to start small. Finetune on fifty or a hundred carefully made examples. If that produces a clear improvement, more data is likely to help. If it produces none, more of the same data rarely will. Then train on a quarter, a half and all of what you have, and plot the result: the shape of that curve tells you how much another batch is worth. Lab 2 shows the usual pattern of early gains that level off.

### Acquiring and annotating data

The most valuable data usually comes from your own application: what your users ask and how they respond. A product that collects such data and uses it to improve itself, attracting more users and more data, has an advantage that is hard to copy.

Otherwise there are public datasets, which need their licences checked, and data you create or buy. Labelling by hand is slow and expensive. The hard part is writing the annotation guideline: a precise statement of what a good response is, with examples, covering the awkward cases. A vague guideline produces inconsistent labels however careful the annotators are. The same guideline can be reused for evaluation, as chapter 4 described.

## Augmentation and synthesis

When real data is scarce, you can create more. Augmentation derives new examples from real ones. Synthesis generates data that imitates the properties of real data.

### Why generate data

- **Quantity.** More examples, cheaply.
- **Coverage.** Examples of situations that are rare in what you collected, such as unusual requests or a class with few samples.
- **Privacy.** Synthetic records can stand in for real ones that cannot be shared.
- **Distillation.** Have a large model produce the examples a small model learns from.

### Traditional techniques

Before language models, synthetic data came from rules and simulation. Templates with slots for names, numbers and phrases can multiply a few hand-written examples into thousands. Small perturbations, such as swapping a word for a synonym, add variety. Simulators produce data for situations that are dangerous or costly to stage, such as driving scenarios.

### Generating with models

Models can now generate training data directly: paraphrase an example, translate it, write new instructions in the style of a few seeds, or work backwards by taking good existing text and writing the instruction it would be the answer to. The last approach has a useful property: the answers were written by people and are of known quality, and only the instructions are generated.

### Verifying what was generated

Generated data is only useful if it is good, and it comes out fluent whether it is right or wrong. It has to be checked.

- Where an answer can be tested, test it: run the code, recompute the sum.
- Otherwise use a model as a judge, with the limitations described in chapter 3.
- Apply cheap filters as well: drop examples that are too short or too long, repetitive, or near-copies of others.

Lab 3 shows a generator that is wrong 8% of the time and a functional check that removes every wrong example.

### The limits of generated data

- **Quality control** is hard at volume, and unchecked errors go straight into the model.
- **Superficial imitation.** A model trained on another model's outputs may learn the surface, such as the look of step-by-step reasoning, without the ability behind it.
- **Model collapse.** When models are trained repeatedly on generated data, each generation under-represents rare cases a little more, and over time the variety in the data disappears. Keeping real data in the mix is the remedy.
- **Obscured lineage.** If the generating model was trained on data with restrictions, or on a benchmark you intend to test with, those problems carry through into your dataset without leaving a trace.

### Distillation

**Distillation** trains a small model, the student, to imitate a large one, the teacher. The teacher's outputs become the student's training data. The result is cheaper and faster to run and can come close to the teacher on a narrow task. Check the teacher's licence first, since some forbid using outputs to train a competing model.

:::checkpoint[A team generates 100,000 training examples with a large model and finetunes a small model on them without looking at any. What should worry you?]
Nobody knows how many of the examples are wrong, and wrong examples are fluent. The small model will learn the errors along with everything else. At minimum a sample should be read by a person, checkable answers should be checked automatically, and duplicates and malformed examples should be filtered out.
:::

## Data processing

Whatever the source, data needs the same handling before training.

- **Inspect it.** Look at the data yourself. Compute simple statistics: lengths, the most common words, how labels are distributed. Then read a few dozen examples. Fifteen minutes of reading regularly reveals problems that no metric showed.
- **Deduplicate.** Repeated examples skew what the model learns, and if copies end up in both the training and the test set, they inflate your scores. Exact copies are easy to find by hashing. Near-copies need a similarity measure and a threshold, and the threshold matters: too strict misses reworded copies, too loose deletes examples that are merely alike. Lab 1 measures both errors.
- **Clean and filter.** Remove leftover markup, personal information, toxic content and anything that breaks your policies. Remove examples that are simply low quality.
- **Format.** Put every example into exactly the structure the model expects, including the chat template from chapter 5. A formatting mistake here is quiet and expensive: training runs without complaint and the model comes out worse.

Some steps are much cheaper than others. Do the cheap ones first so that the costly ones run on less data.

## What the labs show

- **Lab 1** plants 450 copies of three kinds in a dataset and compares exact hashing, normalized hashing and similarity search at three thresholds.
- **Lab 2** trains a classifier on growing amounts of data, then on data with a consistent labelling mistake.
- **Lab 3** multiplies three seed examples with templates, verifies a careless generator, and trains repeatedly on generated data.
