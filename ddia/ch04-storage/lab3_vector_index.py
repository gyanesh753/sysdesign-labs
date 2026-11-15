# lab3_vector_index.py - DDIA Ch 4: exact nearest-neighbour search versus an approximate HNSW index
import time

import hnswlib
import numpy as np

rng = np.random.default_rng(4)
N, DIM, K, QUERIES = 50_000, 64, 10, 300
centres = rng.normal(size=(200, DIM))                       # embeddings cluster by topic, so fake some topics
data = (centres[rng.integers(0, 200, N)] + 0.35 * rng.normal(size=(N, DIM))).astype(np.float32)
data /= np.linalg.norm(data, axis=1, keepdims=True)
queries = (centres[rng.integers(0, 200, QUERIES)] + 0.35 * rng.normal(size=(QUERIES, DIM))).astype(np.float32)
queries /= np.linalg.norm(queries, axis=1, keepdims=True)

# Flat index: compare the query with every vector. Exact, and the cost grows with N.
t = time.perf_counter()
truth = np.argsort(-(queries @ data.T), axis=1)[:, :K]
flat_ms = (time.perf_counter() - t) * 1000 / QUERIES
print(f'{N:,} vectors of {DIM} dimensions, top {K} for {QUERIES} queries\n')
print(f'{"index":<22}{"build":>9}{"per query":>12}{"recall@10":>12}')
print(f'{"flat (exact)":<22}{"-":>9}{flat_ms:>10.2f}ms{1.0:>12.3f}')

index = hnswlib.Index(space='cosine', dim=DIM)
index.init_index(max_elements=N, ef_construction=100, M=16, random_seed=4)
t = time.perf_counter()
index.add_items(data, np.arange(N))
build = time.perf_counter() - t
for ef in [10, 40, 160]:                                     # ef = how many candidates the search keeps open
    index.set_ef(ef)
    t = time.perf_counter()
    found, _ = index.knn_query(queries, k=K, num_threads=1)
    ms = (time.perf_counter() - t) * 1000 / QUERIES
    recall = np.mean([len(set(found[i]) & set(truth[i])) / K for i in range(QUERIES)])
    print(f'{"HNSW, ef=" + str(ef):<22}{build:>8.1f}s{ms:>10.3f}ms{recall:>12.3f}')
