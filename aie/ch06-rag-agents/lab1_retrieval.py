# lab1_retrieval.py - AIE Ch 6: term-based retrieval, embedding-based retrieval, and the two combined
import numpy as np
import requests
from rank_bm25 import BM25Okapi

# A made-up company handbook. Each entry is one retrievable document.
DOCS = [
    'Employees may work from another country for up to 30 days a year with their manager\'s approval.',
    'Annual leave is 24 days. Unused days can be carried over until the end of March.',
    'Expense claims must be submitted within 60 days with a photo of each receipt.',
    'The office is closed on public holidays. A skeleton support team stays on call.',
    'New laptops are issued every three years. Report a damaged laptop to the IT desk.',
    'Error E-4417 means the payment gateway rejected the card. Ask the customer to try another card.',
    'Error E-2090 means the session expired. The customer needs to sign in again.',
    'Product KC-220 is the 1 kg bag of dark roast beans. It ships in two days.',
    'Product KC-315 is the ceramic pour-over set. It ships in five days.',
    'Refunds are issued to the original payment method within seven working days.',
    'Parents are entitled to 26 weeks of paid leave after the birth or adoption of a child.',
    'The company matches retirement contributions up to five percent of salary.',
    'Visitors must sign in at reception and wear a badge at all times.',
    'Passwords must be at least 14 characters long and are changed once a year.',
    'Lost access cards must be reported to security the same day.',
    'Training budgets are 40,000 rupees per person per year and need approval in advance.',
    'Overtime is paid at one and a half times the normal hourly rate.',
    'The cafeteria serves lunch from noon until two in the afternoon.',
    'Customer data may not be copied to personal devices under any circumstances.',
    'Shuttle buses leave the metro station every twenty minutes during rush hour.',
    # several look-alike codes: easy for exact matching, confusing for a model of meaning
    'Error E-4471 means the payment gateway timed out. Ask the customer to wait a minute and retry.',
    'Error E-4717 means the payment gateway is down for maintenance. Tell the customer to try later.',
    'Error E-2900 means the session was opened on another device. The customer must sign out there.',
    'Product KC-202 is the 250 g bag of dark roast beans. It ships in two days.',
    'Product KC-222 is the 1 kg bag of light roast beans. It ships in three days.',
    'Product KC-351 is the glass pour-over set. It ships in five days.',
]
# (question, index of the document that answers it, kind of question)
QUERIES = [
    ('Can I do my job from abroad for a few weeks?', 0, 'meaning'),
    ('How much holiday do I get?', 1, 'meaning'),
    ('When do I get reimbursed for money I spent on a business trip?', 2, 'meaning'),
    ('How much time off do new mothers and fathers receive?', 10, 'meaning'),
    ('Does the employer add to my pension savings?', 11, 'meaning'),
    ('Is there money available for courses and conferences?', 15, 'meaning'),
    ('What does E-4417 mean?', 5, 'exact term'),
    ('E-2090', 6, 'exact term'),
    ('KC-315 delivery time', 8, 'exact term'),
    ('What is KC-220?', 7, 'exact term'),
    ('customer sees E-4717', 21, 'exact term'),
    ('KC-222', 24, 'exact term'),
]

STOPWORDS = set('a an the is are do does i my me we to of for in on at and or it its be can how much what when there any get with from by this that'.split())
tokenize = lambda s: [w for w in s.lower().replace('?', ' ').replace('.', ' ').replace(',', ' ').split() if w not in STOPWORDS]
bm25 = BM25Okapi([tokenize(d) for d in DOCS])


def embed(texts, kind):
    # this embedding model expects a prefix saying whether the text is a query or a document
    r = requests.post('http://localhost:11434/api/embed', json={'model': 'nomic-embed-text', 'input': [f'{kind}: {t}' for t in texts]}, timeout=120)
    v = np.array(r.json()['embeddings'])
    return v / np.linalg.norm(v, axis=1, keepdims=True)


doc_vectors = embed(DOCS, 'search_document')
query_vectors = embed([q for q, _, _ in QUERIES], 'search_query')


def rank_terms(i):
    return list(np.argsort(-bm25.get_scores(tokenize(QUERIES[i][0]))))


def rank_embeddings(i):
    return list(np.argsort(-(doc_vectors @ query_vectors[i])))


def rank_hybrid(i, k=60, embedding_weight=1.0):
    """Reciprocal rank fusion: a document's score is the sum of weight / (k + its rank) over both rankings."""
    score = np.zeros(len(DOCS))
    for ranking, weight in ((rank_terms(i), 1.0), (rank_embeddings(i), embedding_weight)):
        for position, doc in enumerate(ranking):
            score[doc] += weight / (k + position + 1)
    return list(np.argsort(-score))


print(f'{len(DOCS)} documents, {len(QUERIES)} questions. Each cell: right document ranked first / right document in the top 3\n')
print(f'{"retriever":<34}{"questions by meaning":>22}{"questions with an exact code":>30}')
RETRIEVERS = [('term-based (BM25)', rank_terms), ('embedding-based', rank_embeddings), ('hybrid, equal weights', rank_hybrid),
              ('hybrid, embeddings weighted 3x', lambda i: rank_hybrid(i, embedding_weight=3.0))]
for name, rank in RETRIEVERS:
    cells = []
    for kind in ('meaning', 'exact term'):
        rows = [(rank(i), answer) for i, (_, answer, k_) in enumerate(QUERIES) if k_ == kind]
        first = np.mean([r[0] == a for r, a in rows])
        top3 = np.mean([a in r[:3] for r, a in rows])
        cells.append(f'{first:.0%} / {top3:.0%}')
    print(f'{name:<34}{cells[0]:>22}{cells[1]:>30}')

print('\nWhere each one goes wrong:')
for name, rank in [('term-based', rank_terms), ('embedding-based', rank_embeddings)]:
    for i, (q, answer, _) in enumerate(QUERIES):
        got = rank(i)[0]
        if got != answer:
            print(f'  {name:<16} "{q}"\n{"":<19}-> retrieved: {DOCS[got][:70]}...')
