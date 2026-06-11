"""
chunk.py — Stage 2 of the Unofficial Guide pipeline: recursive, token-aware chunking.

Reads the cleaned documents from documents/clean/ (produced by ingest.py) and
splits each into ~150-token chunks with ~15-token overlap, measured with the
SAME tokenizer the embedding model (all-MiniLM-L6-v2) uses — so the token counts
here match what the model will actually see and nothing gets silently truncated
at its 256-token cap.

Chunking is recursive and structure-aware: it splits on paragraph/comment
boundaries first (blank lines), then sentences, then words, only falling back to
a hard token limit when a single piece is still too large.

Every chunk carries metadata: its source filename and its index within that doc.

Run this stage alone:
    python chunk.py                 # print total chunk count + per-source counts
    python chunk.py --samples 5     # also print 5 sample chunks with source + token length
"""

from __future__ import annotations

import argparse
import re
from functools import lru_cache
from pathlib import Path

CLEAN_DIR = Path(__file__).parent / "documents" / "clean"

CHUNK_SIZE = 150      # target tokens per chunk (per planning.md)
CHUNK_OVERLAP = 15    # token overlap between adjacent chunks
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


# ---------------------------------------------------------------------------
# Token counting — uses the embedding model's own tokenizer
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _tokenizer():
    # AutoTokenizer loads ONLY the tokenizer files for all-MiniLM-L6-v2 (small,
    # cached after first download) — not the full embedding model. This makes our
    # token counts identical to what the model tokenizes at embedding time.
    from transformers import AutoTokenizer, logging as hf_logging
    # We only COUNT tokens (no truncation), so silence the harmless
    # "sequence longer than 512" warning the tokenizer emits on big blocks.
    hf_logging.set_verbosity_error()
    return AutoTokenizer.from_pretrained(MODEL_NAME)


def count_tokens(text: str) -> int:
    # add_special_tokens=False: count only the content tokens, excluding the
    # [CLS]/[SEP] markers the model adds — we care about budget for real text.
    return len(_tokenizer().encode(text, add_special_tokens=False))


# ---------------------------------------------------------------------------
# Recursive splitting
# ---------------------------------------------------------------------------

def _split_by_words(text: str, chunk_size: int) -> list[str]:
    """Last-resort split: pack words into windows up to chunk_size tokens.
    Only reached when a single sentence exceeds the chunk size."""
    words = text.split()
    out, cur = [], []
    for w in words:
        cur.append(w)
        if count_tokens(" ".join(cur)) > chunk_size:
            cur.pop()
            if cur:
                out.append(" ".join(cur))
            cur = [w]
    if cur:
        out.append(" ".join(cur))
    return out


def _split_oversized_block(block: str, chunk_size: int) -> list[str]:
    """A paragraph/comment larger than chunk_size: split on sentence boundaries,
    then fall back to words for any sentence that is still too large."""
    sentences = re.split(r"(?<=[.!?])\s+", block.strip())
    units = []
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if count_tokens(s) <= chunk_size:
            units.append(s)
        else:
            units.extend(_split_by_words(s, chunk_size))
    return units


def _tail_overlap(text: str, overlap: int) -> str:
    """Return the trailing ~overlap tokens of `text` (whole words), used to seed
    the start of the next chunk so a fact split across a boundary stays retrievable."""
    if overlap <= 0:
        return ""
    words = text.split()
    tail: list[str] = []
    for w in reversed(words):
        tail.insert(0, w)
        if count_tokens(" ".join(tail)) >= overlap:
            break
    return " ".join(tail)


def split_text(text: str, chunk_size: int = CHUNK_SIZE,
               overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Recursive, structure-aware split of one cleaned document into chunks."""
    # 1) Atomic units: paragraph/comment blocks, splitting any oversized block.
    blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
    units: list[str] = []
    for b in blocks:
        if count_tokens(b) <= chunk_size:
            units.append(b)
        else:
            units.extend(_split_oversized_block(b, chunk_size))

    # 2) Greedily pack consecutive units into chunks up to chunk_size tokens,
    #    closing a chunk just before a unit would push it over the limit.
    raw_chunks: list[str] = []
    cur: list[str] = []
    cur_tokens = 0
    for u in units:
        ut = count_tokens(u)
        if cur and cur_tokens + ut > chunk_size:
            raw_chunks.append("\n\n".join(cur))
            cur, cur_tokens = [], 0
        cur.append(u)
        cur_tokens += ut
    if cur:
        raw_chunks.append("\n\n".join(cur))

    # 3) Add overlap by prepending the tail of the previous chunk to each chunk.
    chunks: list[str] = []
    for i, c in enumerate(raw_chunks):
        if i > 0:
            tail = _tail_overlap(raw_chunks[i - 1], overlap)
            if tail:
                c = tail + "\n\n" + c
        chunks.append(c.strip())

    # Drop any empty / whitespace-only chunks.
    return [c for c in chunks if c.strip()]


# ---------------------------------------------------------------------------
# Corpus-level chunking with metadata
# ---------------------------------------------------------------------------

def load_clean_docs() -> list[dict]:
    if not CLEAN_DIR.exists():
        raise FileNotFoundError(
            f"{CLEAN_DIR} not found. Run `python ingest.py` first to produce cleaned docs.")
    files = sorted(CLEAN_DIR.glob("*.txt"))
    if not files:
        raise FileNotFoundError(f"No cleaned .txt files in {CLEAN_DIR}. Run `python ingest.py`.")
    return [{"source_filename": p.name, "clean_text": p.read_text(encoding="utf-8")}
            for p in files]


def chunk_corpus() -> list[dict]:
    """Chunk every cleaned document. Returns
    [{'text', 'source', 'chunk_index'}, ...] with chunk_index per source doc."""
    out = []
    for doc in load_clean_docs():
        for idx, chunk in enumerate(split_text(doc["clean_text"])):
            out.append({
                "text": chunk,
                "source": doc["source_filename"],
                "chunk_index": idx,
            })
    return out


# ---------------------------------------------------------------------------
# Fixed-size chunking (stretch: chunking strategy comparison)
# ---------------------------------------------------------------------------

def split_text_fixed(text: str, chunk_size: int = CHUNK_SIZE,
                     overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Naive baseline: slice the tokenized document into fixed token windows,
    ignoring sentence/review/comment boundaries. Same size and overlap as the
    recursive splitter so the only difference is structure-awareness."""
    tok = _tokenizer()
    ids = tok.encode(text, add_special_tokens=False)
    step = max(1, chunk_size - overlap)
    chunks = []
    for start in range(0, len(ids), step):
        window = ids[start:start + chunk_size]
        if not window:
            continue
        piece = tok.decode(window).strip()
        if piece:
            chunks.append(piece)
        if start + chunk_size >= len(ids):
            break
    return chunks


def chunk_corpus_fixed() -> list[dict]:
    """Same as chunk_corpus() but using the fixed-size splitter."""
    out = []
    for doc in load_clean_docs():
        for idx, chunk in enumerate(split_text_fixed(doc["clean_text"])):
            out.append({
                "text": chunk,
                "source": doc["source_filename"],
                "chunk_index": idx,
            })
    return out


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Chunk documents/clean/ and report.")
    parser.add_argument("--samples", type=int, default=0,
                        help="Print N sample chunks with source + token length.")
    args = parser.parse_args()

    chunks = chunk_corpus()
    total = len(chunks)

    # Per-source counts
    per_source: dict[str, int] = {}
    for c in chunks:
        per_source[c["source"]] = per_source.get(c["source"], 0) + 1

    print(f"Total chunks: {total}  (target window: {CHUNK_SIZE} tokens, "
          f"overlap: {CHUNK_OVERLAP})")
    if total < 50:
        print("  ⚠ fewer than 50 chunks — chunks may be too large.")
    elif total > 2000:
        print("  ⚠ more than 2000 chunks — chunks may be too small.")
    print("\nChunks per source:")
    for src in sorted(per_source):
        print(f"  {src:<40} {per_source[src]:>4}")

    if args.samples > 0:
        step = max(1, total // args.samples)
        picks = chunks[::step][: args.samples]
        print(f"\n--- {len(picks)} sample chunks "
              f"(every {step}th chunk, spread across the corpus) ---")
        for c in picks:
            toks = count_tokens(c["text"])
            print(f"\n[{c['source']} #{c['chunk_index']}] - {toks} tokens")
            print(c["text"])


if __name__ == "__main__":
    main()
