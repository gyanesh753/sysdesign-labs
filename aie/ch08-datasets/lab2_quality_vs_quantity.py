# lab2_quality_vs_quantity.py - AIE Ch 8: how much data, and how clean? A classifier trained on different mixes
import numpy as np

rng = np.random.default_rng(8)
FEATURES, CLASSES = 30, 5
centres = rng.normal(size=(CLASSES, FEATURES))


def make(n):
    y = rng.integers(0, CLASSES, n)
    return centres[y] + rng.normal(size=(n, FEATURES)) * 2.2, y


def train_and_test(X, y, steps=300):
    W = np.zeros((FEATURES, CLASSES))
    for _ in range(steps):
        logits = X @ W
        p = np.exp(logits - logits.max(axis=1, keepdims=True))
        p /= p.sum(axis=1, keepdims=True)
        p[np.arange(len(y)), y] -= 1
        W -= 0.3 * X.T @ p / len(y)
    return (np.argmax(X_test @ W, axis=1) == y_test).mean()


X_test, y_test = make(5_000)


def corrupt(y, share):
    """Systematic labelling error: a share of class 0 is recorded as class 1, as a confused annotator would do."""
    y = y.copy()
    zeros = np.flatnonzero(y == 0)
    y[rng.choice(zeros, int(len(zeros) * share), replace=False)] = 1
    return y


print('PART A  more data helps, and then it stops helping')
print(f'  {"training examples":>18}{"test accuracy":>15}{"gain from doubling":>20}')
previous = None
for n in [50, 100, 200, 400, 800, 1_600, 3_200, 6_400]:
    acc = np.mean([train_and_test(*make(n)) for _ in range(12)])
    print(f'  {n:>18,}{acc:>15.1%}' + (f'{acc - previous:>+20.1%}' if previous is not None else f'{"":>20}'))
    previous = acc

print('\nPART B  clean against noisy: accuracy on class 0, the class the annotators kept getting wrong')
print(f'  {"training set":<52}{"overall":>9}{"on class 0":>12}')


def report(label, n, share):
    scores = []
    for _ in range(5):
        X, y = make(n)
        W_y = corrupt(y, share)
        W = np.zeros((FEATURES, CLASSES))
        for _ in range(300):
            logits = X @ W
            p = np.exp(logits - logits.max(axis=1, keepdims=True))
            p /= p.sum(axis=1, keepdims=True)
            p[np.arange(len(W_y)), W_y] -= 1
            W -= 0.3 * X.T @ p / len(W_y)
        pred = np.argmax(X_test @ W, axis=1)
        scores.append(((pred == y_test).mean(), (pred[y_test == 0] == 0).mean()))
    overall, class0 = np.mean(scores, axis=0)
    print(f'  {label:<52}{overall:>9.1%}{class0:>12.1%}')


report('500 examples, all labels correct', 500, 0.0)
report('5,000 examples, 30% of class 0 mislabelled', 5_000, 0.3)
report('5,000 examples, 60% of class 0 mislabelled', 5_000, 0.6)
report('50,000 examples, 60% of class 0 mislabelled', 50_000, 0.6)
print('  Ten or a hundred times more data does not repair a consistent labelling mistake. The model learns the mistake.')
