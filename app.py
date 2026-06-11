"""
app.py — Stage 5c: Gradio query interface.

A minimal web UI over ask() from query.py: type a question, get a grounded
answer plus the source documents it was retrieved from.

    python app.py
    # then open http://localhost:7860
"""

import gradio as gr

from query import ask


# Maps the source-type dropdown label to the doc_type filter value.
_DOC_TYPE = {"All": None, "Reddit": "reddit", "RateMyProfessors": "rmp"}


def handle_query(question, source_type, course):
    result = ask(
        question,
        doc_type=_DOC_TYPE.get(source_type),
        course=course.strip() or None,
    )
    if result["sources"]:
        sources = "\n".join(f"• {s}" for s in result["sources"])
    else:
        sources = "(no sources, outside the corpus)"
    return result["answer"], sources


with gr.Blocks() as demo:
    gr.Markdown("# The Unofficial Guide\nAsk about UC Berkeley CS courses & professors. "
                "Answers come only from real student reviews and Reddit threads.")
    inp = gr.Textbox(label="Your question")
    with gr.Row():
        source_type = gr.Dropdown(
            ["All", "Reddit", "RateMyProfessors"], value="All",
            label="Filter by source type")
        course = gr.Textbox(label="Filter by course (optional, e.g. CS61B)")
    btn = gr.Button("Ask")
    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Textbox(label="Retrieved from", lines=4)
    inputs = [inp, source_type, course]
    btn.click(handle_query, inputs=inputs, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inputs, outputs=[answer, sources])

demo.launch()
