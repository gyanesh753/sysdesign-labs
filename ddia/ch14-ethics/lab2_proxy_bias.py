# lab2_proxy_bias.py - DDIA Ch 14: removing a sensitive attribute from the data does not remove it from the model
import numpy as np

rng = np.random.default_rng(14)
N = 200_000


def applicants(n):
    group = rng.choice(['A', 'B'], n)
    # The two groups live in different places: 85% of group B in postcodes 0-3, 85% of group A in postcodes 4-9.
    in_b_area = rng.random(n) < np.where(group == 'B', 0.85, 0.15)
    postcode = np.where(in_b_area, rng.integers(0, 4, n), rng.integers(4, 10, n))
    income = rng.normal(50, 15, n).clip(10, 120)            # identical income distribution for both groups
    return group, postcode, income


# History: loan officers approved anyone with income above 45, but demanded 60 from group B. That is the bias.
group, postcode, income = applicants(N)
approved = income > np.where(group == 'B', 60, 45)
print('Historical decisions (made by people)')
for g in 'AB':
    print(f'  group {g}: {approved[group == g].mean():.1%} approved')

# "Fair" model: the group column is deleted. It learns from postcode and income only, by copying past approval rates.
band = (income // 5).astype(int)
table = np.zeros((10, 30))
count = np.zeros((10, 30))
np.add.at(table, (postcode, band), approved)
np.add.at(count, (postcode, band), 1)
rate = table / np.maximum(count, 1)


def model(postcode, income):
    return rate[postcode, (income // 5).astype(int)] >= 0.5

print(f'\nThe model never sees the group. Its agreement with the historical decisions: {(model(postcode, income) == approved).mean():.1%}')

g2, p2, i2 = applicants(N)                                   # new applicants
decision = model(p2, i2)
print('\nModel decisions on new applicants')
for g in 'AB':
    print(f'  group {g}: {decision[g2 == g].mean():.1%} approved')

mid = (i2 > 47) & (i2 < 58)                                  # people who would repay equally well: same income band
print('\nSame income (47 to 58), different outcome')
for g in 'AB':
    print(f'  group {g}: {decision[(g2 == g) & mid].mean():.1%} approved')
print(f'  living in postcodes 0-3: {decision[mid & (p2 < 4)].mean():.1%} approved   living in postcodes 4-9: {decision[mid & (p2 >= 4)].mean():.1%} approved')
print('\nThe postcode stands in for the group. The model reproduced the old bias faithfully, and a high')
print('agreement score made it look like a success.')
