"""
hybrid.py — Stretch feature: hybrid search (BM25 keyword + semantic, fused with RRF).

Motivation: the Q4 evaluation failure ("what is the best professor for CS61A?")
was a retrieval-stage problem. Pure semantic search ranked glowing Garcia
reviews for CS10/CS61C nearly as close as the DeNero CS61A reviews, because the
embedding rewards the generic shape of praise language and gives little weight
to the exact token "CS61A". BM25 keyword search does the opposite. Combining the
two should pull the off-course reviews back down.

Design:
  - Semantic side: reuse the existing retrieve() (all-MiniLM-L6-v2 + ChromaDB).
  - Keyword side: a BM25 index (rank-bm25) over the same 851 chunks.
  - Fuse the two rankings with Reciprocal Rank Fusion (RRF), which merges by rank
    position so we never have to normalize cosine distances against BM25 scores
    (they live on different scales).

The semantic-only retrieve() in retrieve.py is left untouched so the baseline
stays available for the comparison.

    python hybrid.py "What is the best professor for CS61A?"
"""

from __future__ import annotations

import argparse
import re
from functools import lru_cache

from rank_bm25 import BM25Okapi

from chunk import chunk_corpus
from retrieve import retrieve

RRF_K = 60     # standard RRF constant; dampens the weight of top ranks
POOL = 20      # how many results to pull from each method before fusing


def _tokenize(text: str) -> list[str]:
    """Lowercase word/number tokens for BM25. Course codes like 'cs61a' stay
    intact as single tokens, which is exactly the signal we want to weight."""
    return re.findall(r"[a-z0-9]+", text.lower())


@lru_cache(maxsize=1)
def _bm25_index():
    """Build the BM25 index over the same chunks the vector store holds.
    Cached so it is built once per process."""
    chunks = chunk_corpus()
    by_id = {f"{c['source']}_{c['chunk_index']}": c for c in chunks}
    ids = list(by_id.keys())
    tokenized = [_tokenize(by_id[i]["text"]) for i in ids]
    return BM25Okapi(tokenized), ids, by_id


def _bm25_rank(query: str, pool: int) -> list[str]:
    """Return the ids of the top-`pool` chunks by BM25 score, best first."""
    bm25, ids, _ = _bm25_index()
    scores = bm25.get_scores(_tokenize(query))
    order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    return [ids[i] for i in order[:pool]]


def retrieve_hybrid(query: str, k: int = 5, pool: int = POOL) -> list[dict]:
    """Hybrid retrieval. Returns the top-k fused chunks as
    {text, source, chunk_index, rrf_score, in_semantic, in_bm25}."""
    _, _, by_id = _bm25_index()

    # Semantic ranking (reuse the existing pipeline, just ask for more results).
    sem = retrieve(query, k=pool)
    sem_ids = [f"{r['source']}_{r['chunk_index']}" for r in sem]

    # Keyword ranking.
    bm_ids = _bm25_rank(query, pool)

    # Reciprocal Rank Fusion: each method contributes 1 / (RRF_K + rank).
    scores: dict[str, float] = {}
    for rank, cid in enumerate(sem_ids, start=1):
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (RRF_K + rank)
    for rank, cid in enumerate(bm_ids, start=1):
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (RRF_K + rank)

    ranked = sorted(scores, key=lambda c: scores[c], reverse=True)[:k]

    results = []
    for cid in ranked:
        c = by_id[cid]
        results.append({
            "text": c["text"],
            "source": c["source"],
            "chunk_index": c["chunk_index"],
            "rrf_score": round(scores[cid], 5),
            "in_semantic": cid in sem_ids,
            "in_bm25": cid in bm_ids,
        })
    return results


def main():
    parser = argparse.ArgumentParser(description="Hybrid (BM25 + semantic) search.")
    parser.add_argument("query", help="The question / search string.")
    parser.add_argument("--k", type=int, default=5, help="Number of results (default 5).")
    args = parser.parse_args()

    results = retrieve_hybrid(args.query, k=args.k)
    print(f'Query: {args.query!r}   (hybrid: BM25 + semantic, fused with RRF)\n')
    for rank, r in enumerate(results, start=1):
        methods = []
        if r["in_semantic"]:
            methods.append("semantic")
        if r["in_bm25"]:
            methods.append("bm25")
        print(f"#{rank}  rrf={r['rrf_score']:.5f}  found by: {', '.join(methods)}  "
              f"[{r['source']} #{r['chunk_index']}]")
        print(r["text"])
        print("-" * 80)


if __name__ == "__main__":
    main()
