"""
retrieve.py — Stage 4 of the Unofficial Guide pipeline: semantic search.

Embeds a user query with the SAME model used to build the index
(all-MiniLM-L6-v2) and returns the top-k nearest chunks from the persistent
ChromaDB collection, each with its source, position, and cosine distance.

Query and document vectors must come from the same model and be compared with
the same metric (cosine) for the distances to be meaningful — that is why this
file mirrors index.py's model + normalization choices.

Run:
    python retrieve.py "Is CS61A harder in the spring with Garcia than fall with DeNero?"
    python retrieve.py "your query" --k 8
"""

from __future__ import annotations

import argparse
from functools import lru_cache
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_DIR = str(Path(__file__).parent / "chroma_db")
COLLECTION_NAME = "unofficial_guide"
MODEL_NAME = "all-MiniLM-L6-v2"


# Load the model and open the collection ONCE per process (not per query), so
# repeated calls — in the CLI or later the Gradio UI — don't reload the model.
@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


@lru_cache(maxsize=1)
def _collection():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    try:
        return client.get_collection(COLLECTION_NAME)
    except Exception as e:
        raise RuntimeError(
            f"Collection '{COLLECTION_NAME}' not found at {CHROMA_DIR}. "
            f"Run `python index.py` first to build the index."
        ) from e


def retrieve(query: str, k: int = 5) -> list[dict]:
    """Return the top-k chunks most semantically similar to `query`.

    Each result: {text, source, chunk_index, distance}, ordered nearest first.
    `distance` is COSINE distance (range 0–2, lower = more similar)."""
    # Embed the query exactly as the documents were embedded in index.py:
    # same model, normalized to unit length.
    query_embedding = _model().encode([query], normalize_embeddings=True).tolist()

    # query() finds the nearest stored vectors. We ask Chroma to return the
    # stored document text and metadata alongside the distances so we don't need
    # a second lookup. (Embeddings are not returned — we don't need them here.)
    res = _collection().query(
        query_embeddings=query_embedding,
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    # Chroma returns each field as a list-of-lists (one inner list per query);
    # we sent a single query, so we read index [0] of each.
    documents = res["documents"][0]
    metadatas = res["metadatas"][0]
    distances = res["distances"][0]

    return [
        {
            "text": doc,
            "source": md.get("source"),
            "chunk_index": md.get("chunk_index"),
            "distance": dist,
        }
        for doc, md, dist in zip(documents, metadatas, distances)
    ]


def main():
    parser = argparse.ArgumentParser(description="Semantic search over the chunk index.")
    parser.add_argument("query", help="The question / search string.")
    parser.add_argument("--k", type=int, default=5, help="Number of results (default 5).")
    args = parser.parse_args()

    results = retrieve(args.query, k=args.k)
    print(f'Query: {args.query!r}   (top {len(results)}, cosine distance — lower is closer)\n')
    for rank, r in enumerate(results, start=1):
        print(f"#{rank}  distance={r['distance']:.4f}  "
              f"[{r['source']} #{r['chunk_index']}]")
        print(r["text"])
        print("-" * 80)


if __name__ == "__main__":
    main()
