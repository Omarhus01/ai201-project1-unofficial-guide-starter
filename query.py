"""
query.py — Stage 5b: end-to-end entry point.

ask(question) ties the pipeline together:
    retrieve.py (top-k chunks)  ->  distance guard  ->  generate.py  ->  sources

Two-layer refusal:
  Layer 1 — distance guard: if even the closest retrieved chunk is farther than
            DISTANCE_THRESHOLD (cosine), nothing in the corpus is relevant, so we
            return the refusal WITHOUT calling the LLM. Handles out-of-corpus
            questions (e.g. a professor not in our documents).
  Layer 2 — the grounded system prompt in generate.py: for questions that pass
            the guard but still aren't answerable from the retrieved text, the
            model returns the REFUSAL phrase itself.

Source attribution is built HERE from chunk metadata (deduped source filenames),
never parsed from the model's output. On any refusal, sources is an empty list.

    python query.py "Does DeNero teach the CS61A lectures himself?"
"""

from __future__ import annotations

import argparse

from generate import REFUSAL, generate_answer
from retrieve import retrieve

# Cosine distance above which we treat the best match as "not relevant" and
# refuse before calling the LLM. Tune after observing real out-of-corpus
# distances (in-corpus good answers ran ~0.18–0.49).
DISTANCE_THRESHOLD = 0.6

TOP_K = 5


def ask(question: str) -> dict:
    """Return {"answer": str, "sources": list[str]}.

    sources is the deduplicated list of source filenames of the retrieved
    chunks — empty whenever the system refuses (either layer)."""
    chunks = retrieve(question, k=TOP_K)

    # Layer 1: distance guard. retrieve() returns results sorted nearest-first,
    # so chunks[0] is the closest. If it's beyond the threshold, refuse.
    best_distance = chunks[0]["distance"] if chunks else float("inf")
    if best_distance > DISTANCE_THRESHOLD:
        return {"answer": REFUSAL, "sources": []}

    answer = generate_answer(question, chunks)

    # Layer 2: the model itself judged the context insufficient. No grounded
    # answer means no sources to attribute.
    if answer.strip() == REFUSAL:
        return {"answer": REFUSAL, "sources": []}

    # Programmatic attribution: distinct source filenames, preserving the
    # retrieval order (closest first).
    sources = list(dict.fromkeys(c["source"] for c in chunks))
    return {"answer": answer, "sources": sources}


def main():
    parser = argparse.ArgumentParser(description="Ask the Unofficial Guide a question.")
    parser.add_argument("question", help="The question to answer.")
    args = parser.parse_args()

    result = ask(args.question)
    print("\nAnswer:")
    print(result["answer"])
    print("\nSources:")
    if result["sources"]:
        for s in result["sources"]:
            print(f"  • {s}")
    else:
        print("  (none — outside the corpus)")


if __name__ == "__main__":
    main()
