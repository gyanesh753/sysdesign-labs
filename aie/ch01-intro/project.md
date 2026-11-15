## Goal

Take the mystery out of three things: how a model can learn from unlabelled text, what a token is, and what actually happens when you call a model.

Labs 1 and 2 are plain Python with no dependencies. Lab 3 calls a model running on your machine through Ollama, so the Ollama app has to be open and at least one chat model pulled.

## Lab 1: a language model built by counting

```bash
python lab1_language_model.py
```

The script generates 3,000 simple sentences from a small made-up grammar, then counts which token follows each pair of tokens. That table of counts is the whole model.

**What you should observe**

- Part A: one sentence yields several training examples, each a context and the token that follows, with no labelling.
- Part B: after "the engineer" the model spreads probability over a few verbs. After "predicts the" it is split between two continuations.
- Part C: always taking the most likely token gives the same sentence every time. Sampling gives different, equally grammatical sentences.
- Part D: to fill the blank in "the ___ predicts the answer", the left context alone cannot choose; using the word on the right picks "model".

The final line explains why this approach stops at two tokens of context.

**Try**

1. Change the model to use one token of context instead of two. What nonsense does it start generating, and why?
2. Add 200 sentences of a different style to the corpus. How do the probabilities in Part B change?

## Lab 2: a subword tokenizer

```bash
python lab2_tokens.py
```

Byte-pair encoding starts with single characters and repeatedly merges the most frequent neighbouring pair into a new token.

**What you should observe**

- With no merges the sample sentence takes 43 tokens. With 40 merges it takes 13, and "testing" becomes "test" and "ing".
- With 150 merges every training word is a single token and the vocabulary is simply the list of words.
- With 40 merges, unseen words are still split into known pieces: "retesting" contains "test" and "ing", while "zzz" falls back to single letters.

**Try**

1. Add the word "tokenization" to the training text fifty times and retrain with 40 merges. How is "tokenizer" split now?
2. Print the first twenty merge rules. Which kinds of fragments are learned first?

## Lab 3: a real model

```bash
python lab3_first_call.py
```

**What you should observe**

- Part A: at temperature 0 the same prompt gives the same answer twice.
- Part B: at a high temperature five calls give several different answers.
- Part C: a 300-word preamble raises the input from about 20 tokens to several hundred, and the call takes longer. Asking for a list makes the output, and the time, grow.
- Part D: two questions of six words each, one in English and one in Hindi, use different numbers of tokens.

Your exact numbers depend on which model you have pulled.

**Try**

1. Set `max_tokens` to 5 in Part C's last request. What does the model return, and does it know it was cut off?
2. Ask a factual question the model cannot know, such as today's weather where you are. How confident does the answer sound?

## Write up in NOTES.md

Record the Part B probabilities from lab 1, the table from lab 2, and the Part C table from lab 3. Then answer: pick an AI feature you use. Is the AI critical or complementary there, and is a human in the loop?
