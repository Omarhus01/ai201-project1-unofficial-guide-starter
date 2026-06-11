# The Unofficial Guide

A retrieval-augmented question answering system over real, unofficial UC Berkeley CS student opinion from Reddit and RateMyProfessors. You ask a plain-language question and get an answer grounded only in the collected documents, with the source documents named. If the corpus does not cover the question, the system says so instead of guessing.

## Demo Video

A 3 to 5 minute walkthrough of the system: https://www.loom.com/share/0bd9705658f242d3ac5ee1901f5a6e48

## Running the System

1. Create and activate a virtual environment, then install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and add your free Groq API key as `GROQ_API_KEY` (from console.groq.com).
3. Build the pipeline:
   ```
   python ingest.py    # clean the 26 raw documents into documents/clean/
   python chunk.py      # chunk and report the total count (optional check)
   python index.py      # embed all chunks into a persistent ChromaDB store
   ```
4. Ask questions:
   ```
   python query.py "your question"   # command line
   python app.py                      # Gradio UI at http://localhost:7860
   ```

Pipeline stages: `documents/` to `ingest.py` (clean) to `chunk.py` (chunk) to `index.py` (embed and store in ChromaDB) to `retrieve.py` (semantic search) to `generate.py` (grounded answer) to `query.py` and `app.py` (entry points).

---

## Domain

This system covers real, unofficial student opinion about UC Berkeley CS courses and professors. The documents come from two places students actually use: r/berkeley threads and RateMyProfessors review pages. The corpus focuses on core lower-division courses (CS61A, CS61B, EECS) and on specific professors who teach them, including DeNero, Garcia, Hilfinger, Rao, Shewchuk, and Yokota.

This knowledge is valuable because it answers questions official sources do not. Course catalogs and department pages list requirements, prerequisites, and logistics. They do not tell you how hard a class actually is, how a professor teaches, how heavy the workload runs, or whether one semester graded harder than another. That information only exists in what students say to each other, and it is spread across hundreds of separate threads and reviews. This system makes that scattered opinion searchable and answers questions from it directly, with the source documents named.

---

## Document Sources

26 documents total: 6 RateMyProfessors pages and 20 r/berkeley Reddit threads, all stored as plain text in `documents/`. The set covers four subtopics: professor-specific reviews, course difficulty, course sequencing, and general CS-major perspective.

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | John DeNero reviews (CS61A) | RateMyProfessors | [documents/rmp_denero.txt](https://www.ratemyprofessors.com/professor/1621181) |
| 2 | Dan Garcia reviews (CS61A) | RateMyProfessors | [documents/rmp_garcia.txt](https://www.ratemyprofessors.com/professor/142865) |
| 3 | Paul Hilfinger reviews (CS61B) | RateMyProfessors | [documents/rmp_hilfinger.txt](https://www.ratemyprofessors.com/professor/525740) |
| 4 | Satish Rao reviews | RateMyProfessors | [documents/rmp_rao.txt](https://www.ratemyprofessors.com/professor/226535) |
| 5 | Jonathan Shewchuk reviews | RateMyProfessors | [documents/rmp_shewchuk.txt](https://www.ratemyprofessors.com/professor/246561) |
| 6 | Justin Yokota reviews | RateMyProfessors | [documents/rmp_yokota.txt](https://www.ratemyprofessors.com/professor/2868089) |
| 7 | General opinion on EECS major | Reddit (r/berkeley) | [documents/reddit_best_EECS_1.txt](https://www.reddit.com/r/berkeley/comments/1s4r2m1/opinion_on_eecs/) |
| 8 | Course advice for freshman EECS | Reddit (r/berkeley) | [documents/reddit_best_EECS_2.txt](https://www.reddit.com/r/berkeley/comments/1u0u86w/course_advice_freshman_eecs/) |
| 9 | Best professor for EECS16A | Reddit (r/berkeley) | [documents/reddit_best_EECS_3.txt](https://www.reddit.com/r/berkeley/comments/nsh4e4/best_professor_for_eecs_16a/) |
| 10 | Major recommendations for EECS | Reddit (r/berkeley) | [documents/reddit_best_EECS_4.txt](https://www.reddit.com/r/berkeley/comments/hkk0aw/major_recommendations_for_a_lifeless_eecs_major/) |
| 11 | Must-take CS upper divs | Reddit (r/berkeley) | [documents/reddit_cs_course_sequencing_1.txt](https://www.reddit.com/r/berkeley/comments/122ea3o/musttake_cs_upper_divs/) |
| 12 | Easiest CS upper div to take | Reddit (r/berkeley) | [documents/reddit_cs_course_sequencing_2.txt](https://www.reddit.com/r/berkeley/comments/18thykq/easiest_cs_upper_div_to_take/) |
| 13 | CS upper div recommendations | Reddit (r/berkeley) | [documents/reddit_cs_course_sequencing_3.txt](https://www.reddit.com/r/berkeley/comments/13rz111/cs_upper_divs_class_recommendations/) |
| 14 | Still pursuing CS (difficulty) | Reddit (r/berkeley) | [documents/reddit_cs_difficulty_1.txt](https://www.reddit.com/r/berkeley/comments/1n3cdw7/anyone_here_still_pursuing_cs/) |
| 15 | How hard to get into CS major | Reddit (r/berkeley) | [documents/reddit_cs_difficulty_2.txt](https://www.reddit.com/r/berkeley/comments/1dsep0y/cs_majors_how_hard_is_it_to_get_accepted_as_a_cs/) |
| 16 | Computer science is hard | Reddit (r/berkeley) | [documents/reddit_cs_difficulty_3.txt](https://www.reddit.com/r/berkeley/comments/1gcn9hp/computer_science_is_hard/) |
| 17 | CS61A difficulty, spring vs fall | Reddit (r/berkeley) | [documents/reddit_cs61a_denero_1.txt](https://www.reddit.com/r/berkeley/comments/1ty5qfw/cs61a_question/) |
| 18 | Does DeNero teach 61A lectures | Reddit (r/berkeley) | [documents/reddit_cs61a_denero_2.txt](https://www.reddit.com/r/berkeley/comments/1fap17h/does_denero_actually_teach_the_cs61a_lectures/) |
| 19 | 61A John DeNero | Reddit (r/berkeley) | [documents/reddit_cs61a_denero_3.txt](https://www.reddit.com/r/berkeley/comments/1fjkvcx/61a_john_denero/) |
| 20 | Review of CS61B with Hilfinger | Reddit (r/berkeley) | [documents/reddit_CS61B_Hilfinger_1.txt](https://www.reddit.com/r/berkeley/comments/gp4mf9/review_of_cs61b_with_hilfinger/) |
| 21 | Hilfinger teaching 61A spring 2021 | Reddit (r/berkeley) | [documents/reddit_CS61B_Hilfinger_2.txt](https://www.reddit.com/r/berkeley/comments/j8mzop/hilfinger_teaching_61a_for_spring_2021/) |
| 22 | Avoiding Hilfinger 61B next sem | Reddit (r/berkeley) | [documents/reddit_CS61B_Hilfinger_3.txt](https://www.reddit.com/r/berkeley/comments/dlc7e5/should_i_be_avoiding_hilfinger_61b_next_semester/) |
| 23 | Strategy for studying 61B with Hilfinger | Reddit (r/berkeley) | [documents/reddit_CS61B_Hilfinger_4.txt](https://www.reddit.com/r/berkeley/comments/emvhaf/strategy_for_studying_61b_with_hilfinger/) |
| 24 | Opinion on CS classes | Reddit (r/berkeley) | [documents/reddit_Opinion_on_CS_major_1.txt](https://www.reddit.com/r/berkeley/comments/1btbpq5/my_opinion_on_cs_classes/) |
| 25 | Worst professor and why | Reddit (r/berkeley) | [documents/reddit_professor_recommendation_1.txt](https://www.reddit.com/r/berkeley/comments/1g6zgn1/who_was_your_worst_professor_and_why/) |
| 26 | Most iconic professor | Reddit (r/berkeley) | [documents/reddit_professor_recommendation_2.txt](https://www.reddit.com/r/berkeley/comments/gpcanj/for_better_or_for_worse_who_is_the_most_iconic/) |

---

## Chunking Strategy

**Chunk size:** about 150 tokens, measured with the all-MiniLM-L6-v2 tokenizer so the counts match what the embedding model actually sees.

**Overlap:** about 15 tokens.

**Preprocessing before chunking:** Cleaning is done per source type, chosen by the filename prefix (`ingest.py`). For Reddit files, the loader strips the UI scaffolding (Upvote, Downvote, Reply, Award, Share, usernames, relative timestamps, vote counts, flair, and nav text) and keeps the post title, post body, and comment text, with one comment per paragraph. For RateMyProfessors files, each review is reformatted into a single line that keeps the course, date, numeric ratings (quality, difficulty), would-take-again, grade, and the written review text, while dropping the rating-distribution widget, the "similar professors" list, and the page nav and footer. Every file also has its UTF-8 BOM removed, HTML entities unescaped, and whitespace normalized.

**Chunking method:** Recursive and structure-aware (`chunk.py`). It splits on paragraph and comment boundaries first, then on sentences, then on words, and only falls back to a hard token cut when a single piece is still too large. Pieces are packed up to the 150-token target, and the overlap is added by prepending the trailing 15 tokens of the previous chunk to the next one.

**Why these choices fit your documents:** The substantive units in this corpus are short. A single RMP review or a single Reddit comment is usually a sentence or two. A larger chunk would glue several unrelated opinions together and dilute the match, while a much smaller chunk would lose the subject (an opinion with no professor or course attached). 150 tokens is large enough to hold one full opinion with the context around it and small enough to stay precise. It also sits well under the 256-token limit of all-MiniLM-L6-v2, so no chunk is silently truncated at embedding time. The 15-token overlap matters most for the Reddit files, where opinion on one question is spread across a post and its replies, so a fact that straddles a boundary stays retrievable from either side. For the short RMP reviews the overlap costs almost nothing.

**Final chunk count:** 851 chunks across the 26 documents, which sits inside the healthy 50 to 2,000 range.

### Sample Chunks

Five chunks pulled straight from the index, each labeled with its source document and token count. The `[Course · Date] Quality X/5, Difficulty Y/5` prefix on the RMP chunks is the structured line produced by cleaning.

**1. `reddit_cs61a_denero_1.txt` (chunk 0, 99 tokens)**
> CS61A question Is CS61A harder in the spring? I looked on berkeleytime and the grade averages for spring with Dan Garcia are WAY LOWER than fall with John DeNero. As an incoming freshman, I have a lot of experience with python and java but was thinking of doing CS10 in the fall and then CS61A in the spring but after seeing the grade averages in the fall vs spring, would it be worth it to just take 61A this fall instead?

**2. `rmp_hilfinger.txt` (chunk 57, 123 tokens)**
> to stick to watching the lecture videos at x1.5 on youtube.
>
> [CS61B · Jun 20th, 2014] Quality 4.5/5, Difficulty 5.0/5, Grade: A. CS61B with Hilfinger was easily the most time consuming class I've taken at Berkeley, but the material itself is not terribly difficult. The projects took me between 50-100 hours each, and there are 4 of them. No regrets at all, every CS major should take 61B with Hilfinger. Once the bleeding stops, you'll realize you learned something.

**3. `rmp_denero.txt` (chunk 186, 147 tokens)**
> Amazing. Perfect guy for students' first CS prof when they come to Berkeley.
>
> [CS61A · Mar 12th, 2015] Quality 5.0/5, Difficulty 3.0/5, Grade: A+. I've never rated a professor before, but, like Yeezus, this man is a god.
>
> [CS61A · Feb 15th, 2015] Quality 5.0/5, Difficulty 5.0/5. Simply amazing.
>
> [CS61A · Feb 11th, 2015] Quality 5.0/5, Difficulty 1.0/5. OMG He is my fav prof. I believe everyone who has taken cs61a with him would LOVE computer science.

**4. `rmp_garcia.txt` (chunk 7, 136 tokens)**
> 5.0/5, Grade: Drop/Withdrawal. Good lectures, bad organization.
>
> [CS61A · May 27th, 2026] Quality 1.0/5, Difficulty 4.0/5, Grade: B. Don't be fooled! While he may seem warm and passionate on the outside and talks proudly about his "As for All" belief, the two classes he taught this semester (Spring 2026), CS61A and CS10, had an average of a C+. While in previous semesters taught by another professor (John DeNero) has a consistent average of a B+. Garcia's exams are very unfair!

**5. `reddit_cs61a_denero_2.txt` (chunk 0, 129 tokens)**
> Does Denero actually teach the CS61A lectures? These past few lectures have all been taught by his TA (who is absolutely wonderful btw). Does he actually teach the lectures himself? Why do people always say he's a good teacher?
>
> intent isnt to be rude but does anyone wonder why people say denero is a good lecturer? i feel like he was just fine but nothing special... to me a good lecturer makes it easy to logically follow "why" you do a step, aka the intuition behind things, whereas i felt like denero missed that often
>
> His prerecorded videos are pretty fire

---

## Embedding Model

**Model used:** all-MiniLM-L6-v2 through sentence-transformers. It runs locally, needs no API key, has no rate limits, and produces 384-dimensional vectors. Chunks are embedded with `normalize_embeddings=True` and stored in a persistent ChromaDB collection that uses cosine distance. Queries are embedded with the same model so query and document vectors live in the same space. Retrieval returns the top 5 chunks (top-k = 5).

For this project MiniLM is the right call. It is small, fast, free, and local, and the text is short opinion that does not need a heavyweight model. The 256-token limit is not a problem here because chunks are capped at about 150 tokens by design.

**Production tradeoff reflection:** If this were deployed for real users and cost was not a constraint, two things would change the choice.

First, context length. MiniLM truncates past 256 tokens, so longer units such as a full Reddit comment chain or a long detailed review have to be split before embedding. A model with a larger context window would let me embed longer passages whole and keep a complete opinion and its surrounding discussion in one vector instead of fragmenting it. That matters most for the Reddit shape, where the signal is already spread out.

Second, source variety and credibility, which is more about the data and metadata than the model itself. In production I would widen the corpus beyond Reddit and RMP to other unofficial but credible sources (department forums, vetted student guides, TA write-ups) and attach a source-type and credibility tag to every chunk, so retrieval could weight or filter by it and a confident answer leans on stronger sources rather than a single offhand comment.

Beyond those, the axes I would weigh are accuracy on domain-specific language (course codes, professor nicknames, slang the embedding may not handle well), multilingual support if the user base were not English-only, and latency against the quality gain of a bigger model.

---

## Grounded Generation

Grounding is enforced in two places: the system prompt sent to the model (`generate.py`) and a distance guard that runs before the model is even called (`query.py`). The LLM is Groq's llama-3.3-70b-versatile, called at temperature 0.

**System prompt grounding instruction:** The model is given the retrieved chunks as labeled context passages and these rules, verbatim:

> 1. Answer ONLY using the information in the provided context passages below. You must not use any knowledge outside the provided context, even if you know the answer.
> 2. Do not guess, infer beyond what is stated, or fill gaps with general knowledge.
> 3. If the context does not contain enough information to answer the question, reply with EXACTLY this sentence and nothing else: "I don't have enough information on that."
> 4. When you do answer, base every claim on the context and reflect what students actually said (including disagreement between students, if present).
> 5. Be concise.

The instruction is written as a hard requirement, not a suggestion, and the refusal wording is a single named constant (`REFUSAL`) so the rest of the pipeline can detect it exactly.

**Two-layer refusal.** The grounding prompt is the second of two layers:

- **Layer 1, distance guard (before the LLM):** if the closest retrieved chunk has a cosine distance above 0.6, nothing in the corpus is relevant, so the system returns the refusal with an empty source list and never calls the model. This catches off-domain questions (for example "best pizza in New York", which scored about 0.75).
- **Layer 2, the prompt (rule 3 above):** for questions that pass the guard but still are not answerable from the retrieved text, the model itself returns the refusal sentence. This is what catches a real professor who is not in the corpus (Vern Paxson scored about 0.42, closer than some real in-corpus questions, so the distance guard cannot catch him; the prompt does).

**How source attribution is surfaced in the response:** Sources are built programmatically in `query.py` from the retrieved chunks' metadata. After retrieval, the system takes the distinct `source` filenames of the returned chunks, in retrieval order, and returns them as a separate `sources` list alongside the answer. The model is never asked to write the citations, so attribution does not depend on the model behaving. On either refusal layer the source list is empty, because nothing grounded an answer.

---

## Retrieval Test Results

Three of the five evaluation questions, run through `retrieve.py` with k = 5, showing the top results and their cosine distances (lower is closer). Attributions were checked by grepping distinctive phrases back to the cleaned source files, so every reported source is the file the text actually lives in.

**Query 1: "Is CS61A harder in the spring with Garcia than fall with DeNero?"**

| Rank | Distance | Source (chunk) |
|------|----------|----------------|
| 1 | 0.427 | reddit_cs61a_denero_1.txt (#0) |
| 2 | 0.463 | reddit_cs61a_denero_1.txt (#5) |
| 3 | 0.490 | reddit_cs61a_denero_1.txt (#12) |

*Why these are relevant:* All three come from the exact thread that asks the question, and chunk #12 is the one that explains the cause ("grades were way off this past Spring semester because of new format exam changes"). A fourth and fifth result from `rmp_garcia.txt` add the C+ versus B+ grade comparison. The distances are the highest of the three queries because the question is long and comparative, but the answer-bearing chunks are still in the top results.

**Query 2: "What do students say about Professor Hilfinger's CS61B workload and difficulty?"**

| Rank | Distance | Source (chunk) |
|------|----------|----------------|
| 1 | 0.306 | rmp_hilfinger.txt (#77) |
| 2 | 0.309 | rmp_hilfinger.txt (#57) |
| 3 | 0.343 | rmp_hilfinger.txt (#74) |

*Why these are relevant:* Every top result comes from the correct source, `rmp_hilfinger.txt`, and each chunk is directly about CS61B workload and difficulty. Chunk #57 contains the "projects took me between 50-100 hours each, and there are 4 of them" line and is rated difficulty 5.0/5. The distances of 0.31 to 0.34 reflect a tight, on-topic match.

**Query 3: "Does John DeNero actually teach the CS61A lectures himself?"**

| Rank | Distance | Source (chunk) |
|------|----------|----------------|
| 1 | 0.176 | reddit_cs61a_denero_2.txt (#0) |
| 2 | 0.367 | reddit_CS61B_Hilfinger_2.txt (#0) |
| 3 | 0.377 | rmp_denero.txt (#77) |

*Why these are relevant:* The top result at 0.176 is the exact Reddit thread asking whether DeNero teaches the lectures himself, which is why it scores so close. The fifth-ranked result, a DeNero RMP review saying his "online video lectures are far better than live lecture", supports the recorded-lectures point. The one weaker hit is rank 2, a thread about Hilfinger substituting for 61A, which is on the topic of who teaches 61A but not about DeNero.

---

## Query Interface

The interface is a Gradio web app (`app.py`), run with `python app.py` and opened at `http://localhost:7860`.

**Input field:**
- *Your question:* a text box for the user's question. Pressing the Ask button or Enter submits it.

**Output fields:**
- *Answer:* the grounded answer, or the refusal sentence if the question is out of scope.
- *Retrieved from:* the source documents the answer was retrieved from, one per line, or "(no sources, outside the corpus)" on a refusal.

**Sample interaction transcript:**

> **Your question:** Is CS61A harder in the spring with Garcia than fall with DeNero?
>
> **Answer:** According to the passages, the grade averages for CS61A are lower in the spring with Dan Garcia than in the fall with John DeNero. One student mentions that "the final stats... was worse than the fall" with Garcia, and another student states that Garcia's exams are "very unfair" and that his classes had an average grade of a C+, compared to DeNero's consistent average of a B+. However, another student notes that the difference in grades between fall and spring may be due to "new format exam changes" in the spring semester.
>
> **Retrieved from:**
> reddit_cs61a_denero_1.txt
> rmp_denero.txt
> rmp_garcia.txt

---

## Example Responses

**Grounded answers with source attribution visible:**

Q1, CS61A spring versus fall. Answer cites three sources.

![Q1 spring versus fall](Sample%20tests/good1.png)

Q2, Hilfinger CS61B workload. Answer cites rmp_hilfinger.txt.

![Q2 Hilfinger workload](Sample%20tests/good2.png)

Q3, does DeNero teach the lectures. Hedged answer, cites three sources.

![Q3 DeNero lectures](Sample%20tests/good3.png)

**Out-of-scope refusal (Layer 2, real professor not in the corpus):**

Q5, Vern Paxson. The query passes the distance guard (best distance about 0.42) but the model finds no supporting context and refuses, with no sources.

![Q5 Paxson refusal](Sample%20tests/refusal_layer_2.png)

**Off-domain refusals (Layer 1, distance guard):**

These two questions are not about the domain at all, so the closest chunk is past the 0.6 threshold and the system refuses before calling the LLM.

![Off-domain refusal, pizza](Sample%20tests/refusal_layer_1.png)

![Off-domain refusal, bicycle](Sample%20tests/refusal_layer_1_2.png)

---

## Evaluation Report

All five test questions from `planning.md` were run through the system end to end. Q1 to Q3 are answerable baselines, Q4 is a deliberate lexical-overlap trap, and Q5 is an out-of-corpus refusal test.

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | Is CS61A harder in the spring with Dan Garcia than in the fall with John DeNero? | Yes. Lower spring averages under Garcia versus higher fall averages under DeNero, with the spring difficulty attributed to a harder final and exam-format changes, not the professor alone. | Said spring averages under Garcia are lower than fall under DeNero, cited the "final stats... worse than the fall" comment and the C+ versus B+ comparison, and noted the gap may be due to "new format exam changes". | Relevant | Accurate |
| 2 | What do students say about Professor Hilfinger's CS61B workload and difficulty? | Heavy and demanding: very time-consuming projects (50-100 hours, four of them), fast pace, low hand-holding, but rigorous and respected. | Described very high workload and difficulty, projects of 50-100 hours each with four of them, difficulty rated 5.0/5 with comments like "amazingly hard", but worth it ("every CS major should take 61B with Hilfinger"). | Relevant | Accurate |
| 3 | Does John DeNero actually teach the CS61A lectures himself? | Yes. His lectures are well-regarded and often recorded, to the point that students say live attendance is optional. | Answered with appropriate hedging: some recent lectures were taught by his TA, but he has prerecorded videos and is highly regarded, so he is involved in teaching the course even if not always in person. | Relevant | Accurate |
| 4 | What is the best professor for CS61A? | Diffuse signal. DeNero is generally well-regarded but no single source cleanly answers this; expected to surface a lexical-overlap retrieval failure rather than a clean answer. | Answered DeNero, citing 5.0/5 ratings and quotes like "He is my fav prof" and "this man is a god". Sources listed both `rmp_denero.txt` and `rmp_garcia.txt`. | Partially off-target (3 of 5 chunks were Garcia CS10/CS61C reviews) | Answer accurate, source attribution misleading |
| 5 | What do students think of Professor Vern Paxson's teaching? | No answer available. Paxson is a real Berkeley CS professor deliberately excluded from the corpus, so correct behavior is refusal. | Returned exactly "I don't have enough information on that." with an empty source list. | Off-corpus (best distance about 0.42, passed the distance guard and was refused by the prompt layer) | Accurate (correct refusal) |

**Retrieval quality:** Relevant / Partially relevant / Off-target
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

**Question that failed:** Q4, "What is the best professor for CS61A?" This was built as a trap, and it failed in the way it was meant to, with one extra twist.

**What the system returned:** The answer itself was reasonable: DeNero, supported by 5.0/5 reviews. But the retrieval underneath it was off. Of the five retrieved chunks, only two were about DeNero. The other three were Garcia reviews for CS10 and CS61C, not CS61A. The distances were all low and "good looking" (about 0.32 to 0.35), which hid the problem. Generation survived because the grounding prompt let the model lean on the two relevant DeNero chunks and ignore the rest, but the programmatic source list still cited `rmp_garcia.txt`, a source that did not actually support the answer.

**Root cause (tied to a specific pipeline stage):** This is a retrieval-stage failure. Semantic similarity rewards the generic shape of the language ("best professor", "my fav prof", "amazing", "students"), which is nearly identical across high-praise reviews regardless of which course they describe. So glowing Garcia reviews for CS10 and CS61C scored almost as close to the query as the DeNero CS61A reviews did. The query word "CS61A" carries little weight in a 384-dimensional sentence embedding compared to the overall praise tone, so the course filter that a human would apply instantly is not applied at all. The misleading citation is a second, smaller cause at the attribution stage: the system lists the sources of the whole retrieved set rather than only the chunks the answer actually used, so a source that contributed nothing still appears.

**What you would change to fix it:** The direct fix for the retrieval cause is hybrid search, combining BM25 keyword matching with the semantic search. BM25 would give real weight to the exact token "CS61A" and pull the off-course Garcia reviews back down the ranking. This is the planned stretch feature, chosen specifically because it targets this failure. A lighter alternative is metadata filtering on the course code, since the RMP chunks already carry the course in their text and could carry it as metadata. For the citation cause, attribution could be narrowed so only the sources of chunks the answer relied on are listed, rather than the full retrieved set.

---

## Spec Reflection

**One way the spec helped you during implementation:** The Chunking Strategy section did real work before any code existed. By writing down that the corpus has two shapes (sprawling Reddit threads where opinion is spread across comments, and compact RMP pages where each review is close to a standalone unit) and committing to about 150 tokens with 15 overlap, I had a concrete target when I implemented `ingest.py` and `chunk.py`. The two-shape note told me Reddit needed cleaning that splits on comment boundaries while RMP needed review-boundary structure, and the token numbers told me exactly what to verify (851 chunks, each holding one full opinion, none over the 256-token model limit). The five evaluation questions written in planning, including the Q4 trap and the Q5 Paxson gap, also gave me a fixed set of targets to test retrieval and generation against at every milestone instead of guessing whether things worked.

**One way your implementation diverged from the spec, and why:** The spec planned a single refusal mechanism. Anticipated Challenge #2 in planning.md said the out-of-corpus case would be handled by a grounding prompt that forces "I don't have enough information" when retrieval comes back "empty or weak". During implementation two assumptions in that sentence turned out to be wrong. Retrieval never comes back empty, because ChromaDB always returns k results, and "weak" is not reliably separable by distance: when I measured the Paxson query its best distance was about 0.42, which is actually closer than the legitimate Q1 query at about 0.43. So I added a second layer the plan did not describe: an explicit distance guard in `query.py` (refuse before calling the LLM if the closest chunk is past 0.6) sitting in front of the grounding prompt. The guard catches off-domain questions like "best pizza in New York" cheaply, and the prompt catches on-domain but off-corpus questions like Paxson. This change came directly from measuring real distances rather than from the original plan.

---

## AI Usage

I used Claude Code as the implementation tool, driven one milestone at a time from the spec in planning.md. I reviewed each module before running it and made the design calls myself.

**Instance 1 (ingestion and chunking)**

- *What I gave the AI:* My Documents and Chunking Strategy sections from planning.md and the architecture diagram, with the instruction to build `ingest.py` and `chunk.py` to my stated size and overlap, cleaning Reddit and RMP boilerplate by filename prefix.
- *What it produced:* Per-source cleaning plus a recursive, token-aware chunker.
- *What I changed or overrode:* I directed it to keep dependencies minimal and not pull in LangChain, to count tokens with the actual all-MiniLM-L6-v2 tokenizer so the counts matched the embedding model, and for the RMP files to reformat each review into a single structured line (course, date, ratings, review text) instead of only deleting junk. I verified one cleaned document and inspected sample chunks and the 851 total before moving on.

**Instance 2 (retrieval and generation)**

- *What I gave the AI:* My Retrieval Approach section for the embedding and retrieval step, then the grounding requirement (answer from retrieved context only, refuse otherwise) and the Gradio skeleton for the generation and interface step.
- *What it produced:* `index.py` and `retrieve.py` for embedding and search, then `generate.py`, `query.py`, and `app.py` for grounded generation and the UI.
- *What I changed or overrode:* The generated vector store would have used ChromaDB's default L2 distance; I directed it to cosine so the scores matched the sub-0.5 thresholds the project expects. For generation I required source attribution to be built programmatically from chunk metadata rather than written by the model, and I added the distance-guard refusal layer described in the Spec Reflection after measuring real out-of-corpus distances. I read the system prompt to confirm it enforced grounding before running anything.
