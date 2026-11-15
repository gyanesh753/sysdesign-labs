# lab3_lora.py - AIE Ch 7: low-rank adaptation: change a layer's behaviour by training two small matrices
import numpy as np

rng = np.random.default_rng(7)
D, N = 64, 4_000
W0 = rng.normal(size=(D, D)) / np.sqrt(D)                  # the "pretrained" layer, frozen
# The new task needs W0 plus a change. The change is mostly a few directions (rank 4), with a little everywhere else.
delta = rng.normal(size=(D, 4)) @ rng.normal(size=(4, D)) / np.sqrt(D) + 0.01 * rng.normal(size=(D, D))
W_target = W0 + delta
X = rng.normal(size=(N, D))
Y = X @ W_target.T
baseline = np.mean((X @ W0.T - Y) ** 2)


def train_full(steps=600, lr=0.05):
    W = W0.copy()
    for _ in range(steps):
        W -= lr * 2 * (X @ W.T - Y).T @ X / N
    return np.mean((X @ W.T - Y) ** 2)


def train_lora(rank, steps=3_000, lr=0.02):
    A = rng.normal(size=(rank, D)) * 0.1                   # trained
    B = np.zeros((D, rank))                                # trained; starts at zero so the layer begins unchanged
    for _ in range(steps):
        grad_w = 2 * (X @ (W0 + B @ A).T - Y).T @ X / N     # what the gradient of the full matrix would be
        A, B = A - lr * B.T @ grad_w, B - lr * grad_w @ A.T
    return np.mean((X @ (W0 + B @ A).T - Y) ** 2), A, B


print(f'one layer, {D} x {D} = {D * D:,} weights. Error before any training: {baseline:.3f}\n')
print(f'{"method":<26}{"trained values":>16}{"share of the layer":>20}{"error after training":>22}{"error removed":>15}')
full = train_full()
print(f'{"full finetuning":<26}{D * D:>16,}{1:>20.0%}{full:>22.4f}{1 - full / baseline:>15.1%}')
for rank in [1, 2, 4, 8, 16]:
    loss, A, B = train_lora(rank)
    print(f'{"LoRA, rank " + str(rank):<26}{2 * D * rank:>16,}{2 * D * rank / (D * D):>20.0%}{loss:>22.4f}{1 - loss / baseline:>15.1%}')
print('  The change this task needs is mostly 4 directions, so rank 4 captures nearly all of it and higher ranks add little.')

loss, A, B = train_lora(4)
merged = W0 + B @ A
same = np.allclose(X @ merged.T, X @ W0.T + X @ A.T @ B.T)
print(f'\nAfter training, the two small matrices can be folded into the layer: W0 + B x A gives identical outputs: {same}')
print('  So the adapted model is exactly as fast as the original. Or keep them separate and swap adapters per task.')

print('\nAt real sizes the saving is far larger:')
for d, rank in [(4_096, 8), (4_096, 64), (8_192, 16)]:
    print(f'  layer {d:,} x {d:,} = {d * d / 1e6:,.1f} M weights; rank {rank} adapter = {2 * d * rank / 1e6:.2f} M values ({2 * d * rank / (d * d):.2%})')
