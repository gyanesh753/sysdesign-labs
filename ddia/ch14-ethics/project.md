## Goal

See two of the chapter's warnings happen in a few lines of code, with the true state of the world known, so that you can see exactly how far the system's picture drifts from it.

Both labs are plain Python simulations and run in a second. The scenarios and numbers are made up for illustration.

## Lab 1: a feedback loop

```bash
python lab1_feedback_loop.py
```

Two districts have exactly the same real rate of violations. A hundred inspectors are divided between them each round. The starting split is 55 to 45.

**What you should observe**

- Rule 1 sends inspectors where the most violations were recorded. Within five rounds one district has 98 of the 100 inspectors, and it stays that way. That district then accounts for about 99% of all recorded violations.
- Rule 2 sends inspectors according to violations found per inspector. The split wanders around 50 to 50 for all 25 rounds.

Under rule 1 the data looks like overwhelming evidence that one district is the problem. It is evidence of where the inspectors were.

**Try**

1. Start rule 1 from an exact 50 to 50 split. Does it stay balanced? What does that say about how small a starting bias needs to be?
2. Reserve 10 inspectors each round to be assigned at random, outside the rule. How does that change rule 1?
3. Give district B a true rate of 0.12. Which rule finds out?

## Lab 2: bias through a proxy

```bash
python lab2_proxy_bias.py
```

200,000 past loan applications. Both groups have identical incomes. Loan officers approved group A above an income of 45 and demanded 60 from group B. The two groups mostly live in different postcodes. A model is then trained on postcode and income only.

**What you should observe**

- Historical approval rates: about 63% for group A and 25% for group B.
- The model never sees the group, and agrees with the historical decisions about 94% of the time.
- On new applicants it approves about 57% of group A and 31% of group B.
- Among applicants with the same middle income, about 85% of group A are approved and 15% of group B. In that income band the decision is determined entirely by postcode.

**Try**

1. Remove postcode from the model as well. What happens to the gap, and to the agreement score? What would you expect if another field also correlated with group?
2. Reduce the residential separation from 85% to 60%. How much of the gap remains?
3. The historical labels are the problem. What data would you need in order to train on whether loans were actually repaid, and why is that data itself incomplete?

## Write up in NOTES.md

Record the inspector split at rounds 1, 5 and 25 under both rules, and the four pairs of approval rates from lab 2. Then answer: think of a system you have worked on that scores, ranks or filters people. Which field in its data could be standing in for something you would not want it to use?
