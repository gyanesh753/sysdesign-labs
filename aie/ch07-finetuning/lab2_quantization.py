# lab2_quantization.py - AIE Ch 7: storing weights with fewer bits: how much accuracy does each bit buy?
import numpy as np

rng = np.random.default_rng(7)

# A small classifier to quantize: 40 input features, a hidden layer of 64, 6 classes.
N, FEATURES, HIDDEN, CLASSES = 6_000, 40, 64, 6
centres = rng.normal(size=(CLASSES, FEATURES)) * 0.9
labels = rng.integers(0, CLASSES, N)
X = centres[labels] + rng.normal(size=(N, FEATURES)) * 1.6
X_train, y_train, X_test, y_test = X[:4_500], labels[:4_500], X[4_500:], labels[4_500:]

W1 = rng.normal(size=(FEATURES, HIDDEN)) * 0.1
W2 = rng.normal(size=(HIDDEN, CLASSES)) * 0.1
for step in range(400):                                    # plain gradient descent
    h = np.maximum(X_train @ W1, 0)
    logits = h @ W2
    p = np.exp(logits - logits.max(axis=1, keepdims=True))
    p /= p.sum(axis=1, keepdims=True)
    p[np.arange(len(y_train)), y_train] -= 1
    g2 = h.T @ p / len(y_train)
    g1 = X_train.T @ ((p @ W2.T) * (h > 0)) / len(y_train)
    W1 -= 0.5 * g1
    W2 -= 0.5 * g2


def accuracy(a, b):
    return (np.argmax(np.maximum(X_test @ a, 0) @ b, axis=1) == y_test).mean()


def quantize(w, bits):
    """Map every weight to the nearest of 2^bits evenly spaced values between the smallest and largest weight."""
    levels = 2 ** bits - 1
    lo, hi = w.min(), w.max()
    codes = np.round((w - lo) / (hi - lo) * levels)        # what is stored: small integers
    return codes / levels * (hi - lo) + lo                  # what is used at run time


params = W1.size + W2.size
print(f'classifier with {params:,} weights, test accuracy at full precision: {accuracy(W1, W2):.1%}\n')
print(f'{"bits per weight":>16}{"distinct values":>17}{"size":>10}{"largest rounding error":>24}{"test accuracy":>15}')
print(f'{32:>16}{"(float)":>17}{params * 4 / 1024:>8.1f} kB{0:>24.4f}{accuracy(W1, W2):>15.1%}')
for bits in [16, 8, 6, 4, 3, 2, 1]:
    q1, q2 = quantize(W1, bits), quantize(W2, bits)
    error = max(np.abs(q1 - W1).max(), np.abs(q2 - W2).max())
    print(f'{bits:>16}{2 ** bits:>17,}{params * bits / 8 / 1024:>8.1f} kB{error:>24.4f}{accuracy(q1, q2):>15.1%}')
print('\nDown to about 4 bits the accuracy does not move, at an eighth of the size. Below that it starts to fall.')
print('Where the drop begins depends on the model, which is why a quantized model is always evaluated again before use.')
