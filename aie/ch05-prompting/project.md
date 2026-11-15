## Goal

Measure what prompt wording actually changes on a real model, and test a prompt of your own against the standard attacks.

All three labs call a chat model through Ollama, so the Ollama app must be running with at least one chat model pulled. They share a small helper, `llm.py`. Your numbers will differ from the ones below, which came from one particular 9-billion-parameter model; the pattern should be similar.

## Lab 1: three prompts for one task

```bash
python lab1_few_shot.py
```

Twenty support messages, each belonging to one of four categories. "Usable" means the reply is exactly one of the four category words, which is what code reading the reply would need.

**What you should observe**

- The vague prompt produces no usable output at all. The model writes a few hundred characters of analysis per message.
- Clear instructions with definitions produce a usable label every time, about seven characters long, and get nearly all of them right. In my run one message was wrong: a problem with two-factor codes was labelled technical instead of account.
- Adding four examples fixed that last case in my run.

**Try**

1. Remove the category definitions from the few-shot prompt and keep only the examples. Does accuracy hold?
2. Replace the four examples with four that are all from the billing category. What happens to the predictions?

## Lab 2: output a program can read

```bash
python lab2_structured_output.py
```

**What you should observe**

- With no format mentioned, nothing parses.
- With the format described, the model produces correct JSON but wraps it in a markdown code block, so in my run 0 of 8 replies parsed.
- Removing the wrapper in code made all 8 parse, with all 24 fields correct.
- Constrained sampling is tried last. The server I used reported it as unavailable for this model; with a model and server that support it, the reply is guaranteed to match the schema.

**Try**

1. Add "Do not use markdown or code blocks" to the instruction. Does the model comply every time?
2. Add a text with no amount in it. What does each approach return, and what should it return?

## Lab 3: attacking your own prompt

```bash
python lab3_prompt_attacks.py
```

The system prompt sets up a translation assistant and contains a made-up internal code that must never appear in a reply. Seven inputs are sent: one ordinary request and six attempts to extract the prompt, change the task or plant an instruction.

**What you should observe**

In my run:

- With the plain system prompt, six of the seven requests went wrong. The code was leaked twice, the model followed an instruction hidden in the text to be translated, and it wrote a tea recipe in English when told to.
- An output filter that blocks any reply containing the code stopped both leaks. The requests still failed, and the other attacks were untouched.
- The hardened prompt, which wraps the content in tags and says that nothing inside them is an instruction, brought failures down to one of seven, with no leaks.

The pass or fail checks are simple string matches. Print the replies and read them before believing the table.

**Try**

1. Write two new attacks of your own and add them to the list. Does the hardened prompt hold?
2. Count false alarms: send five ordinary sentences that happen to contain words like "ignore" or "system". Does the hardened prompt still translate them?

## Write up in NOTES.md

Record the table from each lab, with your model's name. Then answer: for an application you might build, what could an injected instruction make the model do, and which check outside the model would limit the damage?
