"""
index.py — Stage 3 of the Unofficial Guide pipeline: embed + store.

Loads the chunks produced by chunk.py, embeds each one locally with
all-MiniLM-L6-v2, and stores the vectors + text + source metadata in a
PERSISTENT ChromaDB collection on disk (./chroma_db/). Embedding once and
persisting means retrieval (retrieve.py, Milestone 4 step 2) and the UI
(Milestone 5) can reuse the index without re-embedding every run.

We embed the chunks OURSELVES with sentence-transformers and hand the finished
vectors to Chroma, rather than letting Chroma apply its own default embedding
function. This guarantees the stored vectors come from exactly the same model
(all-MiniLM-L6-v2) we will use to embed queries in retrieve.py — query and
document vectors must live in the same space for similarity to mean anything.

Run:
    python index.py        # (re)build the index from documents/clean/ chunks
"""

from __future__ import annotations

from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from chunk import chunk_corpus

CHROMA_DIR = str(Path(__file__).parent / "chroma_db")
COLLECTION_NAME = "unofficial_guide"
MODEL_NAME = "all-MiniLM-L6-v2"


def build_index() -> int:
    """Embed every chunk and (re)load it into a fresh ChromaDB collection.
    Returns the number of chunks stored."""

    # 1) Get the chunks from the chunking stage (do NOT re-implement chunking).
    chunks = chunk_corpus()
    if not chunks:
        raise RuntimeError("chunk_corpus() returned no chunks. Run `python ingest.py` "
                           "then `python chunk.py` first.")

    texts = [c["text"] for c in chunks]

    # 2) Embed locally with all-MiniLM-L6-v2. normalize_embeddings=True returns
    #    unit-length vectors; combined with the cosine collection below this keeps
    #    distances clean and scale-independent.
    print(f"Loading embedding model: {MODEL_NAME} ...")
    model = SentenceTransformer(MODEL_NAME)
    print(f"Embedding {len(texts)} chunks ...")
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=True,
        batch_size=64,
    ).tolist()

    # 3) Persistent client: writes the index to ./chroma_db/ on disk so it
    #    survives between runs (vs. an in-memory client that vanishes on exit).
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # 4) Make re-runs safe: delete any existing collection so we don't append
    #    duplicate chunks on top of a previous build.
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass  # collection didn't exist yet — fine on a first run

    # hnsw:space="cosine" sets the distance metric to COSINE distance
    # (range 0–2, lower = more similar). Chroma's default is L2 (squared
    # Euclidean); we override it so distances match the thresholds in the spec
    # (top results well below 0.5).
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    # 5) Store everything. Parallel lists, all length == len(chunks):
    #    - ids:        stable unique id per chunk, "<source>_<chunk_index>"
    #    - embeddings: the vectors we computed above
    #    - documents:  the chunk text (so retrieval returns the text directly)
    #    - metadatas:  source filename + position, for attribution later
    ids = [f"{c['source']}_{c['chunk_index']}" for c in chunks]
    # doc_type is derived from the filename prefix and stored as a scalar so the
    # metadata-filtering stretch can restrict retrieval to Reddit or RMP chunks.
    metadatas = [
        {
            "source": c["source"],
            "chunk_index": c["chunk_index"],
            "doc_type": "rmp" if c["source"].startswith("rmp_") else "reddit",
        }
        for c in chunks
    ]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    stored = collection.count()
    print(f"\nStored {stored} chunks in collection '{COLLECTION_NAME}' at {CHROMA_DIR}")
    return stored


if __name__ == "__main__":
    build_index()
