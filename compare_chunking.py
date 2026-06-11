"""
compare_chunking.py — Stretch: chunking strategy comparison.

Builds a second ChromaDB collection from the naive fixed-size chunker
(chunk_corpus_fixed) and compares it against the recursive, structure-aware
collection on the 5 evaluation questions. Chunk size and overlap are identical
(150 / 15), so the only variable is whether chunk boundaries respect structure.

    python compare_chunking.py
"""

from __future__ import annotations

from pathlib import Path

import chromadb

from chunk import chunk_corpus, chunk_corpus_fixed
from retrieve import _model, retrieve  # reuse the same embedding model + baseline retrieval

CHROMA_DIR = str(Path(__file__).parent / "chroma_db")
FIXED_COLLECTION = "unofficial_guide_fixed"

EVAL_QUESTIONS = [
    ("Q1", "Is CS61A harder in the spring with Garcia than fall with DeNero?"),
    ("Q2", "What do students say about Professor Hilfinger's CS61B workload and difficulty?"),
    ("Q3", "Does John DeNero actually teach the CS61A lectures himself?"),
    ("Q4", "What is the best professor for CS61A?"),
    ("Q5", "What do students think of Professor Vern Paxson's teaching?"),
]


def build_fixed_collection():
    """Embed the fixed-size chunks into their own cosine collection."""
    chunks = chunk_corpus_fixed()
    texts = [c["text"] for c in chunks]
    embeddings = _model().encode(texts, normalize_embeddings=True,
                                 batch_size=64, show_progress_bar=False).tolist()

    client = chromadb.PersistentClient(path=CHROMA_DIR)
    try:
        client.delete_collection(FIXED_COLLECTION)
    except Exception:
        pass
    col = client.create_collection(FIXED_COLLECTION, metadata={"hnsw:space": "cosine"})
    col.add(
        ids=[f"{c['source']}_{c['chunk_index']}" for c in chunks],
        embeddings=embeddings,
        documents=texts,
        metadatas=[{"source": c["source"], "chunk_index": c["chunk_index"]} for c in chunks],
    )
    return col, len(chunks)


def retrieve_fixed(col, query: str, k: int = 5) -> list[dict]:
    emb = _model().encode([query], normalize_embeddings=True).tolist()
    res = col.query(query_embeddings=emb, n_results=k,
                    include=["metadatas", "distances"])
    return [{"source": m["source"], "chunk_index": m["chunk_index"], "distance": d}
            for m, d in zip(res["metadatas"][0], res["distances"][0])]


def _fmt(results):
    return [f"{r['source'].replace('.txt','')}#{r['chunk_index']} ({r['distance']:.3f})"
            for r in results]


def main():
    n_recursive = len(chunk_corpus())
    col, n_fixed = build_fixed_collection()
    print(f"Recursive chunks: {n_recursive}   Fixed-size chunks: {n_fixed}\n")

    for tag, q in EVAL_QUESTIONS:
        rec = retrieve(q, k=5)
        fix = retrieve_fixed(col, q, k=5)
        print("=" * 80)
        print(f"{tag}: {q}")
        print(f"  recursive  best={rec[0]['distance']:.3f}")
        for line in _fmt(rec):
            print(f"     {line}")
        print(f"  fixed-size best={fix[0]['distance']:.3f}")
        for line in _fmt(fix):
            print(f"     {line}")


if __name__ == "__main__":
    main()
