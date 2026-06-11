"""
generate.py — Stage 5a of the Unofficial Guide pipeline: grounded generation.

Takes a user question + the chunks retrieved by retrieve.py and asks Groq's
llama-3.3-70b-versatile to answer USING ONLY those chunks. The system prompt
hard-enforces grounding: no outside knowledge, and a fixed refusal phrase when
the context is insufficient.

This module does NOT decide the source list — query.py builds that
programmatically from chunk metadata. generate.py returns only the answer text.

Requires GROQ_API_KEY in .env (free tier: https://console.groq.com).
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

MODEL = "llama-3.3-70b-versatile"
TEMPERATURE = 0          # deterministic, factual — discourages embroidering past context
MAX_TOKENS = 500

# Single source of truth for the refusal wording. Used here (the model is told
# to emit it verbatim) AND in query.py (to detect a refusal and clear sources).
REFUSAL = "I don't have enough information on that."

SYSTEM_PROMPT = f"""You are a question-answering assistant for an "Unofficial Guide" to UC Berkeley CS courses and professors. You answer strictly from student-written context passages provided to you.

RULES:
1. Answer ONLY using the information in the provided context passages below. You must not use any knowledge outside the provided context, even if you know the answer.
2. Do not guess, infer beyond what is stated, or fill gaps with general knowledge.
3. If the context does not contain enough information to answer the question, reply with EXACTLY this sentence and nothing else: "{REFUSAL}"
4. When you do answer, base every claim on the context and reflect what students actually said (including disagreement between students, if present).
5. Be concise."""


# Module-level client so repeated calls (CLI, UI) don't re-create it.
_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise RuntimeError(
                "GROQ_API_KEY not found. Copy .env.example to .env and add your "
                "free Groq key from https://console.groq.com.")
        _client = Groq(api_key=key)
    return _client


def _build_context(chunks: list[dict]) -> str:
    """Format retrieved chunks into a labeled context block. Each chunk is
    tagged with its source filename so the model can ground (and optionally
    cite) per passage."""
    parts = []
    for i, c in enumerate(chunks, start=1):
        parts.append(f"[Passage {i} — source: {c['source']}]\n{c['text']}")
    return "\n\n".join(parts)


def generate_answer(question: str, chunks: list[dict]) -> str:
    """Call the LLM with the grounded system prompt. Returns the answer string
    (which may be the REFUSAL phrase if the model finds the context insufficient)."""
    context = _build_context(chunks)
    user_message = (
        f"Context passages:\n\n{context}\n\n"
        f"---\n"
        f"Question: {question}\n\n"
        f"Answer using ONLY the context passages above."
    )

    response = _get_client().chat.completions.create(
        model=MODEL,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )
    return response.choices[0].message.content.strip()
