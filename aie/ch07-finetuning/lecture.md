## Changing the model

Prompting and retrieval change what you give a model. **Finetuning** changes the model: you continue training a pretrained model on your own examples so that its weights shift towards your task. It rests on transfer learning. The model already knows a great deal from pre-training, so it needs far fewer examples to learn your task than a model starting from nothing.

Finetuning is the most demanding way to adapt a model. It needs data, compute and people who understand training. So the first question is whether you need it at all.

## When to finetune

### Reasons to finetune

- **Quality on a specific task.** A general model may be mediocre at your particular dialect of SQL or your house style. Examples of exactly what you want can raise quality beyond what prompting achieves.
- **Reliable output formats.** If the model must always produce a particular structure, training on that structure is the most dependable way to get it.
- **A smaller, cheaper model.** A small model finetuned on your task can match a much larger general model on that task, at a fraction of the cost and latency. A common way to get the training data is to have the large model produce it, which is called distillation.
- **Shorter prompts.** Behaviour learned in training no longer needs to be explained with instructions and examples on every request.

### Reasons not to

- **Prompting has not been exhausted.** Many teams turn to finetuning after a few casual prompt attempts. Systematic prompting, with examples and a proper test set, often closes the gap.
- **It can make the model worse elsewhere.** A model tuned hard for one task may lose ability on others.
- **It is a commitment.** You need to gather and maintain data, run training, serve the result, and repeat when better base models appear. A model you finetuned last year may be beaten by an untuned model released this year.

### Finetuning or retrieval

The two address different failures, and it helps to ask which one you have.

- If the model gives wrong answers because it **lacks information**, such as facts about your company or anything recent, give it the information. That is retrieval.
- If the model has the information and gives answers in the **wrong form**, such as the wrong format, style or level of detail, change its behaviour. That is finetuning.

Put briefly: retrieval is for facts, finetuning is for form. They combine well. A sensible order of attack is to start with prompting, add examples, add retrieval if information is missing, and finetune if behaviour is still wrong after that.

:::checkpoint[A support assistant answers in the right tone and format but often quotes last year's prices. Should you finetune it on the current price list?]
No. The failure is missing, changing information. Retrieval puts the current prices into the prompt and stays correct when they change. A finetuned model would need retraining with every price change, and would still occasionally recall the old ones.
:::

## Why memory is the bottleneck

### What training has to store

Running a model needs its weights and some working memory for the intermediate results of the calculation.

Training needs more. For every parameter that is being updated, the system also holds a gradient, which says how to change it, and the optimizer keeps additional values per parameter as well. All of that is on top of the weights and the intermediate results.

The number that matters is the count of **trainable parameters**. Reducing it is the most effective way to reduce the memory that training needs.

### Memory arithmetic

The memory for the weights is the number of parameters multiplied by the bytes used for each. For inference, add an allowance for working memory, commonly about a fifth. For training, add the gradients and the optimizer state for whatever is trainable. Lab 1 works through examples: a model that fits comfortably for inference can need several times as much for full finetuning.

### How numbers are stored

Each weight is a number, and how many bits are used to store it sets both memory and precision. Models have traditionally used 32 bits per value. Halving that to 16 halves the memory with almost no loss of quality, and is now routine.

### Quantization

**Quantization** takes this further, storing values in 8 or 4 bits, or even fewer. A model of 7 billion parameters needs 28 GB at 32 bits and 3.5 GB at 4 bits, which is the difference between a server and a laptop.

There are two ways to do it. The usual one quantizes a model after it has been trained, which is simple and is how most models are prepared for deployment. The other makes the model aware of the reduced precision during training, so that it learns to tolerate it; this gives better quality at very low bit counts and is more work.

The cost is accuracy. Down to a certain number of bits the loss is negligible, and below that it grows quickly. Where that point lies differs by model and task, so a quantized model must be evaluated, not assumed to be equivalent.

## Finetuning techniques

### Full, partial and parameter-efficient

**Full finetuning** updates every parameter. It gives the most freedom and needs the most memory and data.

**Partial finetuning** freezes most of the model and updates only some layers, usually those nearest the output. It needs less memory, but it uses its trainable parameters inefficiently: reaching the quality of full finetuning takes a large share of them.

**Parameter-efficient finetuning** aims to get close to full finetuning while training a very small number of values. There are two broad families. One adds small trainable components to the model and leaves the original weights frozen. The other leaves the model completely untouched and learns special input vectors that are placed before the prompt to steer it.

### LoRA

The most widely used method is **LoRA**, low-rank adaptation. The idea is that the change a layer needs for a new task is usually simple in a specific mathematical sense: it can be expressed as the product of two much smaller matrices. So the original weight matrix is frozen, and only the two small matrices are trained.

This has several attractive consequences.

- **Few trainable values.** For a large layer, the pair of small matrices can be well under one percent of the original, so memory for training drops sharply.
- **No added latency.** After training, the product of the two matrices can be added into the original weights, giving a single matrix of the original size. The adapted model runs exactly as fast as the base.
- **Modularity.** Alternatively, keep the small matrices separate. One base model can serve many tasks or customers by switching adapters, each a few megabytes.

The main setting is the rank, which controls the size of the small matrices. A higher rank can express a more complicated change and costs more. Surprisingly low ranks are often enough. Lab 3 shows a rank-4 adapter recovering almost everything full finetuning does when the change needed is mostly four directions.

LoRA is often combined with quantization: the frozen base is held in 4 bits and the adapter is trained in higher precision, which makes it possible to finetune large models on a single consumer GPU.

### Model merging

Finetuning adapts one model. **Merging** combines several models into one. The simplest method adds or averages their weights. A refinement works with the difference between each finetuned model and the common base, so that the abilities of several finetuned models can be added together, or an unwanted behaviour subtracted. Other methods stack layers from different models.

Merging is useful when you want one model that does several tasks, without having the data to train on them all at once, and where memory is tight, since one merged model takes the place of several.

## Finetuning in practice

**Choose the base model deliberately.** A good approach is to test feasibility first with the strongest model you can afford. If finetuning cannot make that one work, a weaker one will not either. Once it works, try smaller models to find the cheapest that still meets the bar. The alternative path is distillation: get a large model working, use it to generate training data, and train a small one on that.

**Mind the main settings.**

- The **learning rate** sets how large each update is. Too high and training is unstable; too low and it takes forever. It is the setting most worth tuning.
- The **batch size** is how many examples are processed per update. Larger batches are steadier and need more memory.
- The number of **epochs** is how many times the model sees the data. Too few and it has not learned; too many and it memorizes the training examples and does worse on new ones. Watch the error on held-out data.

**Decide how much to build.** A provider's finetuning service is the easiest route, with limited control. A framework on your own hardware gives full control and all the responsibility.

## What the labs show

- **Lab 1** computes the memory needed to hold, run and finetune models of several sizes and formats.
- **Lab 2** trains a small classifier and measures its accuracy as its weights are stored in fewer and fewer bits.
- **Lab 3** adapts one layer with full finetuning and with LoRA at several ranks, then folds the adapter back into the layer.
