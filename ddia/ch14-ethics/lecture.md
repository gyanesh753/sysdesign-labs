## Why this chapter is here

Every earlier chapter treated data as an abstract thing to be stored, moved and transformed. But much of the data in real systems describes people: what they bought, where they went, who they talk to, what they are worth. Systems built on that data decide what people see, what they pay, and sometimes whether they get a job or a loan.

Building such systems is not a neutral act. This chapter has no algorithms in it. It is about the consequences of the things the rest of the course teaches you to build, and about the fact that the engineers who build them are among the few people in a position to notice the problems early.

## Predictive analytics

Predicting next week's weather and predicting whether a person will repay a loan use similar techniques. The difference is what happens when the prediction is acted on. A wrong weather forecast is an inconvenience. A wrong prediction about a person can cost them credit, insurance, housing or work.

As automated scoring spreads, a person who is repeatedly scored badly can find themselves shut out of ordinary parts of life by a series of systems that each made a reasonable-looking decision. Being careful with decisions that are hard for the affected person to reverse is the starting point.

### Bias and discrimination

A model learns from historical data. If past decisions were biased, the data records that bias, and a model trained to imitate the data will imitate the bias, now with the appearance of objectivity.

Removing sensitive attributes such as ethnicity or gender from the data does not solve it. Other attributes carry the same information: where someone lives, what they buy, which school they attended. A model will use whichever of those best reproduces the old pattern. Lab 2 trains a model that never sees which group an applicant belongs to and still approves one group at a fraction of the rate of the other, by way of their postcode. Its agreement with the historical decisions is high, which would normally be reported as success.

A model can only describe the past. If we want the future to be fairer than the past, that has to come from a deliberate human choice. It will not emerge from the data.

### Responsibility and accountability

When a person makes a bad decision, there is someone to question and a way to appeal. When a system does, responsibility easily disappears into "the algorithm decided".

A few things follow for systems that affect people:

- Someone must be answerable for the outcome. Automating a decision does not remove the duty of the organization that deployed it.
- The affected person should be able to find out why, and to challenge it. That is hard when the model cannot be explained even by its authors.
- The underlying data may simply be wrong, and the person it describes usually has no way to see or correct it.
- A statistical prediction is about a group. Applying it to an individual means judging one person by what others like them did.

### Feedback loops

A system that acts on its predictions changes the world that produces its next round of data. Sometimes that reinforces itself.

Recommendation is the familiar case: show people more of what they clicked on, they click on what they are shown, and the system grows more confident. Scoring has harsher versions. Someone marked as a poor risk is offered worse terms, struggles under them, and their record then justifies the original mark.

Lab 1 strips this to its minimum. Two districts have exactly the same rate of violations. Inspectors are sent wherever more violations were recorded last time. A slight initial imbalance grows until one district receives nearly all the attention and nearly all the recorded violations, and the records appear to justify the allocation completely.

You cannot find such loops by examining one component. You have to consider the whole cycle, including how people respond to the system, and ask what it amplifies.

:::checkpoint[A fraud model flags transactions from one region more often. Flagged transactions get extra checks, so more fraud is discovered there, and that goes into next month's training data. What should the team worry about?]
The discovered fraud rate now reflects where the system looked as well as where fraud occurs. Retraining on it will raise that region's scores further. The team needs a measure that corrects for how intensively each region was checked, such as the rate found per check, and some checks spread at random.
:::

## Privacy and tracking

### Surveillance

The other half of the subject is the collection itself. When a system stores data a user typed in on purpose, such as a document they wrote, it is plainly working for the user. When it records everything the user does as a side effect, for purposes that mainly benefit someone else, the relationship has changed.

A useful exercise is to describe a tracking system in the plainest terms available: what is recorded, about whom, for how long, and who can see it. If the plain description sounds like surveillance, the softer vocabulary of analytics and personalization does not make it something else. The amount of detail many companies hold about people who are not suspected of anything would once have been beyond the reach of any government.

### Consent and freedom of choice

The usual reply is that users agreed to the terms. For agreement to mean something, a person must understand what they are agreeing to and be able to refuse without serious cost. Often neither holds.

- Hardly anyone can tell from a privacy policy what is collected, how it will be combined with other data, or what will be inferred from it.
- Data about one person exposes others who agreed to nothing: the people in their contacts, their photos, their messages.
- For services that most of one's community uses, or that an employer or school requires, declining is not a realistic option.

### Privacy and use of data

Privacy does not mean keeping everything secret. It means being able to decide what to reveal to whom. People tell a doctor things they would not tell an employer, and that is a decision they make themselves.

When a service gathers data through tracking, the decision passes from the person to the company, which then determines who sees what, usually in whatever way suits its business. The person described no longer has a say.

### Data as assets and power

Companies treat personal data as an asset, and some exist mainly to trade in it. It is as accurate to see it as a hazard that happens to be valuable.

Whatever is stored can be leaked, stolen, subpoenaed, or sold along with the company. Data gathered under one set of laws and one government may later be used under another. When deciding what to keep, the question is not only whether anyone would misuse it today, but who might hold it in the future.

Data is also power. Knowing a great deal about people while they know little about you is a deeply unequal position, and it has mostly accumulated without public discussion.

## Looking ahead

### Remembering the Industrial Revolution

There is a historical parallel. Industrialization produced great wealth, and also polluted rivers, unsafe factories and child labour. It took generations for societies to decide those costs were unacceptable and to put rules in place. Industry was not destroyed by the rules, and almost nobody now would wish them away.

Data-driven technology is at a comparable early stage: the benefits are real, the harms are real, and the rules have not caught up. How we treat personal data now is likely to be judged later in the way we judge early industrial practices.

### Legislation and self-regulation

Data protection laws such as the GDPR say that personal data should be collected for a stated purpose and limited to what that purpose requires. That is directly opposed to the habit, common in our field, of collecting everything in case it proves useful.

Laws help, but they trail the technology and are unevenly enforced. Much rests on the people building the systems. In practice that means:

- Collect less. Data you do not hold cannot leak and needs no protection.
- Delete data when its purpose has been served, instead of keeping it indefinitely.
- Let people see what you hold about them, and let them correct it.
- For decisions that matter, keep a route to human review and be able to state the reasons.
- Ask about any feature: would the people affected be content if they understood exactly how it works?

None of this is a technical problem, and no architecture resolves it. It depends on the choices of the people who build things, which now includes you.

## What the labs show

- **Lab 1** runs a simple feedback loop between two identical districts under two allocation rules.
- **Lab 2** trains a model on biased historical decisions with the sensitive attribute removed, and measures what it does to new applicants.
