# lab2_chunking.py - AIE Ch 6: how the size and overlap of chunks decide what a retriever can find
import random

from rank_bm25 import BM25Okapi

random.seed(6)
DEVICES = ['boiler', 'grinder', 'roaster', 'conveyor', 'chiller', 'compressor', 'filter unit', 'packing arm', 'label printer', 'scale',
           'steam valve', 'dust extractor', 'water softener', 'cooling fan', 'safety gate', 'hopper', 'sealer', 'pallet lift', 'air dryer', 'sensor array']
CONSEQUENCES = ['the warranty is void', 'the line must be stopped', 'a safety inspection is required', 'the batch must be discarded', 'the supervisor must be notified']
FILLER = ['Keep the surrounding area clear at all times.', 'Wear gloves when handling hot surfaces.', 'Record every inspection in the logbook.',
          'Spare parts are kept in the store room on the ground floor.', 'Do not use water near the electrical panel.', 'Report unusual noises to the shift lead.']

# Build a manual: one section per device. The fact about servicing and its consequence are in NEIGHBOURING sentences.
sentences, facts = [], []
for device in DEVICES:
    days, consequence = random.choice([7, 14, 30, 45, 90]), random.choice(CONSEQUENCES)
    section = [f'The {device} is described in this section.'] + random.sample(FILLER, 3)
    section += [f'The {device} must be serviced every {days} days.', f'If this is missed, {consequence}.'] + random.sample(FILLER, 3)
    sentences += section
    facts.append((device, days, consequence))
words = ' '.join(sentences).split()
print(f'manual: {len(DEVICES)} sections, {len(words):,} words\n')


def chunks(size, overlap):
    step = max(1, size - overlap)
    return [' '.join(words[i:i + size]) for i in range(0, len(words), step)]


def evaluate(size, overlap, k=3):
    parts = chunks(size, overlap)
    tokenize = lambda s: s.lower().replace('.', ' ').replace(',', ' ').replace('?', ' ').split()
    bm25 = BM25Okapi([tokenize(p) for p in parts])
    found_interval = found_consequence = 0
    for device, days, consequence in facts:
        scores = bm25.get_scores(tokenize(f'What happens if the {device} is not serviced, and how often is that?'))
        top = [parts[i] for i in sorted(range(len(parts)), key=lambda i: -scores[i])[:k]]
        found_interval += any(f'{device} must be serviced every {days} days' in t for t in top)
        # the consequence sentence never names the device, so it only helps if it sits in the same chunk as the sentence that does
        found_consequence += any(f'{device} must be serviced' in t and consequence in t for t in top)
    n = len(facts)
    return len(parts), found_interval / n, found_consequence / n, k * size


print(f'{"chunk size":>11}{"overlap":>9}{"chunks":>8}{"finds the interval":>20}{"finds interval AND consequence":>32}{"words sent to the model":>25}')
for size, overlap in [(12, 0), (25, 0), (25, 12), (60, 0), (60, 20), (250, 0), (1000, 0)]:
    count, interval, both, sent = evaluate(size, overlap)
    print(f'{size:>11}{overlap:>9}{count:>8}{interval:>20.0%}{both:>32.0%}{sent:>25,}')
print('\nSmall chunks split facts that belong together. Overlap repairs some of that at the cost of more chunks.')
print('Very large chunks find everything, and send the model thousands of words to answer a one-line question.')
