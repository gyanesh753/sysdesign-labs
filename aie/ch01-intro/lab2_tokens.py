# lab2_tokens.py - AIE Ch 1: why models read tokens, not words or characters: train a tiny byte-pair encoder
from collections import Counter

TEXT = ('the model predicts the next token . the engineer tests the model . the engineer is testing the prompt . '
        'a user asks a question and the model answers the question . the team tested the service and deployed the service . '
        'testing and deploying models is engineering . the model is predicting tokens . prediction needs context . '
        'the analyst is querying the database and reading the logs . engineers test prompts and deploy models . ') * 20
words = Counter(TEXT.split())


def train(merges):
    """Start from single characters. Repeatedly merge the most frequent neighbouring pair into one new token."""
    splits = {w: list(w) + ['_'] for w in words}                 # '_' marks the end of a word
    rules = []
    for _ in range(merges):
        pairs = Counter()
        for w, pieces in splits.items():
            for a, b in zip(pieces, pieces[1:]):
                pairs[(a, b)] += words[w]
        if not pairs:
            break
        (a, b), _ = pairs.most_common(1)[0]
        rules.append((a, b))
        for w, pieces in splits.items():
            i, out = 0, []
            while i < len(pieces):
                if i + 1 < len(pieces) and pieces[i] == a and pieces[i + 1] == b:
                    out.append(a + b)
                    i += 2
                else:
                    out.append(pieces[i])
                    i += 1
            splits[w] = out
    return rules


def encode(word, rules):
    pieces = list(word) + ['_']
    for a, b in rules:                                           # apply the learned merges in the order they were learned
        i, out = 0, []
        while i < len(pieces):
            if i + 1 < len(pieces) and pieces[i] == a and pieces[i + 1] == b:
                out.append(a + b)
                i += 2
            else:
                out.append(pieces[i])
                i += 1
        pieces = out
    return pieces


sample = 'the engineer is testing the deployed model'.split()
print(f'{len(words)} distinct words in the training text\n')
print(f'{"merges":>7}{"vocabulary":>12}{"tokens for the sample":>24}   how "testing" is split')
for merges in [0, 10, 40, 150]:
    rules = train(merges)
    vocab = {p for w in words for p in encode(w, rules)}
    n = sum(len(encode(w, rules)) for w in sample)
    print(f'{merges:>7}{len(vocab):>12}{n:>24}   {" ".join(encode("testing", rules))}')

rules = train(40)
print('\nWith 40 merges, words the tokenizer has never seen still come out as known pieces:')
for word in ['tested', 'retesting', 'predictor', 'tokenizer', 'zzz']:
    print(f'  {word:<12} -> {" | ".join(encode(word, rules))}')
print('\nCharacters: tiny vocabulary, long sequences. Whole words: short sequences, but a huge vocabulary and no way to')
print('handle a new word. Subword tokens sit in between, which is why every modern model uses them.')
