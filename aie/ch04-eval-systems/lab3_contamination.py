# lab3_contamination.py - AIE Ch 4: a benchmark score means little if the model saw the test during training
import random

random.seed(4)
PARTS = ['router', 'scheduler', 'cache', 'tokenizer', 'index', 'gateway', 'parser', 'queue', 'planner', 'encoder',
         'limiter', 'balancer', 'sampler', 'ranker', 'validator', 'batcher', 'monitor', 'resolver', 'compiler', 'broker']
ITEMS = ['stale requests', 'large messages', 'failed jobs', 'old entries', 'slow queries', 'empty batches', 'duplicate events', 'unknown tokens',
         'expired sessions', 'oversized prompts', 'partial results', 'late records', 'invalid inputs', 'idle workers', 'cold shards',
         'broken links', 'missing fields', 'retried calls', 'blocked users', 'noisy logs']
ACTIONS = ['drops', 'reorders', 'duplicates', 'delays', 'compresses', 'rejects', 'batches', 'retries']


def make_question(part, item):
    answer = random.choice(ACTIONS)                 # an arbitrary fact about an imaginary system: it cannot be reasoned out
    wrong = random.sample([x for x in ACTIONS if x != answer], 3)
    return {'question': f'What does the {part} do with {item} under high load?', 'answer': answer, 'options': sorted(wrong + [answer])}


benchmark = [make_question(p, i) for p in PARTS for i in ITEMS]     # 400 distinct questions
random.shuffle(benchmark)
leaked = benchmark[:240]                           # 60% of the benchmark was posted on a public forum, with answers
training_text = ' '.join(f'{q["question"]} Answer: {q["answer"]}.' for q in leaked)


class MemorizingModel:
    """Has no understanding at all. It answers correctly only when it has seen the exact question."""

    def __init__(self, text):
        self.memory = {}
        for chunk in text.split('.'):
            if 'Answer:' in chunk:
                q, a = chunk.split(' Answer: ')
                self.memory[q.strip()] = a.strip()

    def answer(self, q):
        return self.memory.get(q['question'], random.choice(q['options']))


model = MemorizingModel(training_text)
score = lambda qs: sum(model.answer(q) == q['answer'] for q in qs) / len(qs)
print(f'benchmark score reported on the leaderboard: {score(benchmark):.0%}\n')


def ngrams(text, n=8):
    words = text.split()
    return {' '.join(words[i:i + n]) for i in range(len(words) - n + 1)}


train_ngrams = ngrams(training_text)
flagged = [q for q in benchmark if ngrams(q['question']) & train_ngrams]       # shares an 8-word sequence with the training data
clean = [q for q in benchmark if not (ngrams(q['question']) & train_ngrams)]
print('Check: does any 8-word sequence from a benchmark question also appear in the training data?')
print(f'  flagged as seen in training: {len(flagged)} questions -> model scores {score(flagged):.0%}')
print(f'  not found in training:       {len(clean)} questions -> model scores {score(clean):.0%}')
fresh = [make_question(f'{p}-v2', i) for p in PARTS for i in ITEMS]   # questions about components that did not exist yet
print(f'  brand-new questions written after the model was trained: {score(fresh):.0%}  (guessing among 4 options is 25%)')
print('\nThe model learned nothing. Its leaderboard score measured how much of the test it had memorized.')
print('Report the score on the clean part, and keep some evaluation data private so it cannot leak at all.')
