"""
ingest.py — Stage 1 of the Unofficial Guide pipeline: load + clean.

Loads every .txt in documents/, strips a UTF-8 BOM, fixes HTML entities,
normalizes whitespace, and applies SOURCE-SPECIFIC cleaning chosen by the
filename prefix:

    reddit_*.txt -> clean_reddit()  (strip Reddit UI scaffolding)
    rmp_*.txt    -> clean_rmp()     (keep prof name + numeric ratings + review text)

Cleaned documents are written to documents/clean/<same_filename> so the
cleaning can be inspected BEFORE chunking. The module also returns the cleaned
docs in memory as a list of {"source_filename", "clean_text"}.

Run this stage alone:
    python ingest.py            # clean all docs, write documents/clean/, print a summary
    python ingest.py --show reddit_cs61a_denero_1.txt   # print one cleaned doc to inspect
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

DOCS_DIR = Path(__file__).parent / "documents"
CLEAN_DIR = DOCS_DIR / "clean"


# ---------------------------------------------------------------------------
# Shared text normalization
# ---------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    """Strip BOM, unescape HTML entities (&amp;, &#39;, &nbsp;), and normalize
    non-breaking spaces. Whitespace WITHIN a line is collapsed later, per line,
    so we preserve line breaks here (the cleaners split on them)."""
    text = text.replace("﻿", "")          # UTF-8 BOM
    text = html.unescape(text)                  # &amp; -> &, &#39; -> ', &nbsp; -> \xa0
    text = text.replace("\xa0", " ")            # non-breaking space -> normal space
    return text


def _norm_line(line: str) -> str:
    """Collapse runs of inner whitespace in a single line and trim the ends."""
    return re.sub(r"[ \t]+", " ", line).strip()


# ---------------------------------------------------------------------------
# Reddit cleaning
# ---------------------------------------------------------------------------

# Exact (lowercased) UI strings that are never content.
_REDDIT_JUNK = {
    "go to berkeley", "go to comments", "view all comments", "single comment thread",
    "continue this thread", "more replies", "load more comments",
    "sort by:", "best", "top", "new", "controversial", "old", "q&a",
    "search comments", "expand comment search", "comments section", "add a comment",
    "share", "reply", "award", "upvote", "downvote", "save", "follow", "report",
    "give award",
}

# Lines that open a new comment/post and act as paragraph boundaries.
_REDDIT_AVATAR = re.compile(r"^u/\S+\s+avatar$", re.IGNORECASE)
# Relative timestamps: "4d ago", "23h ago", "Edited 2d ago", "just now".
_REDDIT_TIME = re.compile(
    r"^(edited\s+)?(\d+\s*(s|sec|secs|m|min|mins|h|hr|hrs|d|w|wk|wks|mo|mos|y|yr|yrs)\s+ago|just now)$",
    re.IGNORECASE,
)
_INT_ONLY = re.compile(r"^-?\d+$")            # bare vote counts


def _is_reddit_junk(line: str) -> bool:
    low = line.lower()
    if low in _REDDIT_JUNK:
        return True
    if _REDDIT_TIME.match(line):
        return True
    if _INT_ONLY.match(line):                 # vote counts like "5", "-3"
        return True
    if low.startswith("profile badge"):       # "Profile Badge for the Achievement ..."
        return True
    if line == "•":                       # stray bullet
        return True
    # Single-token lines with no internal whitespace are scaffolding, not content:
    # usernames (BackgroundCress5018), flair (CS/EECS), button labels, "r/berkeley".
    # Real titles/bodies/comments always contain at least one space.
    if len(line.split()) == 1:
        return True
    return False


def _is_reddit_boundary(line: str) -> bool:
    """Markers that reliably begin a new post/comment header."""
    return line == "•" or bool(_REDDIT_AVATAR.match(line))


def clean_reddit(text: str) -> str:
    """Keep post title, post body, and comment text; drop all UI scaffolding.

    Strategy: walk lines. The avatar line and the '•' bullet mark the start of a
    new comment, so they flush the current paragraph. Everything that survives
    the junk filter is content; consecutive content lines belonging to the same
    comment are joined into one paragraph. Comments are separated by blank lines
    so the chunker can split on comment boundaries.
    """
    paragraphs: list[str] = []
    current: list[str] = []

    def flush():
        if current:
            paragraphs.append(" ".join(current))
            current.clear()

    for raw in normalize_text(text).split("\n"):
        line = _norm_line(raw)
        if not line:
            continue
        if _is_reddit_boundary(line):
            flush()                            # new comment starts here
            continue
        if _is_reddit_junk(line):
            continue
        current.append(line)                   # substantive content
    flush()

    return "\n\n".join(p for p in paragraphs if p.strip())


# ---------------------------------------------------------------------------
# RateMyProfessors cleaning
# ---------------------------------------------------------------------------

_FLOAT = re.compile(r"^\d+(\.\d+)?$")
_PCT = re.compile(r"^(\d+)%$")
_DATE = re.compile(r"^[A-Z][a-z]{2,8}\.?\s+\d{1,2}(st|nd|rd|th)?,\s+\d{4}$")
_KEYVAL = re.compile(r"^([A-Za-z][A-Za-z ]+):\s*(.+)$")
_PROF_LINE = re.compile(r"^Professor in the .+ department at .+$", re.IGNORECASE)


def _is_prose(line: str) -> bool:
    """A written review sentence vs. a tag chip / metadata line.

    Tags ('Caring', 'Lots of homework', 'Tough grader') are short noun phrases
    with no sentence punctuation; reviews are longer or punctuated."""
    if not line or _KEYVAL.match(line) or _FLOAT.match(line) or _DATE.match(line):
        return False
    if len(line.split()) >= 5:
        return True
    return bool(re.search(r"[.!?,;]", line))


def _find_review_starts(lines: list[str]) -> list[int]:
    """Indices where a review block begins: a 'Quality' label immediately
    followed by a number, with a 'Difficulty' label close behind."""
    starts = []
    for i, ln in enumerate(lines):
        if ln.strip() != "Quality":
            continue
        nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
        if not _FLOAT.match(nxt):
            continue
        window = " ".join(lines[i: i + 5])
        if "Difficulty" in window:
            starts.append(i)
    return starts


def _extract_header(header_lines: list[str]) -> str:
    """Build one professor header line from the page's top block."""
    name = quality = difficulty = pct = ratings = None
    for i, ln in enumerate(header_lines):
        s = ln.strip()
        if _PROF_LINE.match(s) and i > 0 and name is None:
            # Professor name is the line right above the "Professor in the ..." line.
            for j in range(i - 1, -1, -1):
                if header_lines[j].strip():
                    name = header_lines[j].strip()
                    break
        if s == "/ 5" and i > 0 and quality is None:
            quality = header_lines[i - 1].strip()
        if s.lower() == "level of difficulty" and i > 0 and difficulty is None:
            difficulty = header_lines[i - 1].strip()
        if pct is None and _PCT.match(s):
            pct = _PCT.match(s).group(1)
        m = re.search(r"Based on (\d+) ratings", s) or re.search(r"^(\d+) Student Ratings$", s)
        if m and ratings is None:
            ratings = m.group(1)

    parts = [f"Professor {name}" if name else "Professor (unknown)"]
    parts.append("Computer Science, UC Berkeley.")
    stats = []
    if quality:
        stats.append(f"overall quality {quality}/5")
    if pct:
        stats.append(f"{pct}% would take again")
    if difficulty:
        stats.append(f"difficulty {difficulty}/5")
    line = " ".join(parts)
    if stats:
        line += " " + ", ".join(stats).capitalize() + "."
    if ratings:
        line += f" Based on {ratings} ratings."
    return line


def _parse_review(block: list[str]) -> str | None:
    """Turn one review block into a single self-contained line."""
    quality = difficulty = course = date = wta = grade = None
    prose: list[str] = []

    for i, raw in enumerate(block):
        s = raw.strip()
        if not s:
            continue
        if s == "Quality" and i + 1 < len(block) and _FLOAT.match(block[i + 1].strip()):
            quality = block[i + 1].strip()
            continue
        if s == "Difficulty" and i + 1 < len(block) and _FLOAT.match(block[i + 1].strip()):
            difficulty = block[i + 1].strip()
            # the line right after the difficulty number is the course code
            if i + 2 < len(block):
                cand = block[i + 2].strip()
                if cand and not _KEYVAL.match(cand) and not _DATE.match(cand) and len(cand) <= 15:
                    course = cand
            continue
        if _DATE.match(s) and date is None:
            date = s
            continue
        kv = _KEYVAL.match(s)
        if kv:
            key, val = kv.group(1).strip().lower(), kv.group(2).strip()
            if key == "would take again":
                wta = val
            elif key == "grade":
                grade = val
            continue
        if _is_prose(s):
            prose.append(s)

    # Assemble. A review with no prose (rating-only) still yields a useful line.
    head = []
    if course:
        head.append(course)
    if date:
        head.append(date)
    tag = f"[{' · '.join(head)}] " if head else ""

    rating_bits = []
    if quality:
        rating_bits.append(f"Quality {quality}/5")
    if difficulty:
        rating_bits.append(f"Difficulty {difficulty}/5")
    if wta:
        rating_bits.append(f"Would take again: {wta}")
    if grade:
        rating_bits.append(f"Grade: {grade}")
    rating = ", ".join(rating_bits)

    text = " ".join(prose).strip()
    if not rating and not text:
        return None
    if text:
        return f"{tag}{rating}. {text}".strip()
    return f"{tag}{rating}.".strip()


def clean_rmp(text: str) -> str:
    """Keep the professor identity + per-review ratings + written review text;
    drop nav, rating-distribution widget, 'similar professors', footer legalese."""
    lines = normalize_text(text).split("\n")
    starts = _find_review_starts(lines)
    if not starts:
        # No detectable reviews — fall back to keeping prose lines only.
        return "\n\n".join(_norm_line(l) for l in lines if _is_prose(_norm_line(l)))

    header = _extract_header(lines[: starts[0]])

    reviews = []
    bounds = starts + [len(lines)]
    for a, b in zip(bounds, bounds[1:]):
        review = _parse_review(lines[a:b])
        if review:
            reviews.append(review)

    return header + "\n\n" + "\n\n".join(reviews)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def clean_document(filename: str, raw: str) -> str:
    if filename.startswith("rmp_"):
        return clean_rmp(raw)
    if filename.startswith("reddit_"):
        return clean_reddit(raw)
    # Unknown prefix: apply only the shared normalization.
    return "\n".join(_norm_line(l) for l in normalize_text(raw).split("\n") if _norm_line(l))


def ingest_documents(write_clean: bool = True) -> list[dict]:
    """Load, clean, and (optionally) write every .txt in documents/.
    Returns [{'source_filename', 'clean_text'}, ...]."""
    files = sorted(p for p in DOCS_DIR.glob("*.txt"))
    if not files:
        raise FileNotFoundError(f"No .txt files found in {DOCS_DIR}")

    if write_clean:
        CLEAN_DIR.mkdir(exist_ok=True)

    docs = []
    for path in files:
        raw = path.read_text(encoding="utf-8")
        clean = clean_document(path.name, raw)
        docs.append({"source_filename": path.name, "clean_text": clean})
        if write_clean:
            (CLEAN_DIR / path.name).write_text(clean, encoding="utf-8")
    return docs


def main():
    parser = argparse.ArgumentParser(description="Clean documents/ into documents/clean/.")
    parser.add_argument("--show", metavar="FILENAME",
                        help="Print the cleaned text of one file and exit (does not write).")
    args = parser.parse_args()

    if args.show:
        path = DOCS_DIR / args.show
        if not path.exists():
            sys.exit(f"No such file: {path}")
        print(clean_document(path.name, path.read_text(encoding="utf-8")))
        return

    docs = ingest_documents(write_clean=True)
    print(f"Cleaned {len(docs)} documents -> {CLEAN_DIR}")
    for d in docs:
        n_chars = len(d["clean_text"])
        n_paras = d["clean_text"].count("\n\n") + 1 if d["clean_text"] else 0
        print(f"  {d['source_filename']:<40} {n_chars:>7} chars, ~{n_paras} blocks")
    print(f"\nInspect a single cleaned file with:\n"
          f"  python ingest.py --show {docs[0]['source_filename']}")


if __name__ == "__main__":
    main()
