# lab1_memory_math.py - AIE Ch 7: will it fit? The arithmetic behind running and finetuning a model
GB = 1e9
BYTES = {'32-bit float': 4, '16-bit float': 2, '8-bit integer': 1, '4-bit integer': 0.5}
MODELS = {'1 billion': 1e9, '7 billion': 7e9, '13 billion': 13e9, '70 billion': 70e9}
DEVICES = {'laptop GPU, 16 GB': 16, 'workstation GPU, 24 GB': 24, 'data-centre GPU, 80 GB': 80}

print('PART A  memory just to hold the weights = number of parameters x bytes per parameter')
print(f'  {"parameters":<12}' + ''.join(f'{name:>16}' for name in BYTES))
for name, n in MODELS.items():
    print(f'  {name:<12}' + ''.join(f'{n * b / GB:>13.1f} GB' for b in BYTES.values()))

print('\nPART B  running the model (inference) needs the weights plus working memory; a common allowance is 20% extra')
print(f'  {"model, format":<32}{"needs":>10}   ' + '   '.join(DEVICES))
for name, n in MODELS.items():
    for fmt in ['16-bit float', '4-bit integer']:
        need = n * BYTES[fmt] * 1.2 / GB
        fits = '   '.join(f'{"fits" if need <= cap else "no":^{len(label)}}' for label, cap in DEVICES.items())
        print(f'  {name + ", " + fmt:<32}{need:>7.1f} GB   {fits}')

print('\nPART C  training needs much more: for every parameter being TRAINED you also store a gradient and optimizer state')
print('  7-billion-parameter model, weights in 16-bit floats, a common optimizer that keeps two extra values per trained parameter')
weights = 7e9 * 2 / GB
print(f'  {"what is trained":<34}{"trainable parameters":>22}{"extra memory for training":>28}{"total":>10}')
for label, fraction in [('everything (full finetuning)', 1.0), ('1% of the parameters', 0.01), ('0.1% (a small adapter)', 0.001)]:
    trainable = 7e9 * fraction
    extra = trainable * 4 * 3 / GB                      # gradient + two optimizer values, kept in 32-bit floats
    print(f'  {label:<34}{trainable:>22,.0f}{extra:>25.1f} GB{weights * 1.2 + extra:>7.1f} GB')
print('  Full finetuning needs several times the memory of inference. Training a small fraction of the parameters brings')
print('  the requirement back down to roughly what inference needs, which is the whole point of parameter-efficient methods.')
