"""
app.py — Stage 5c: Gradio query interface.

A minimal web UI over ask() from query.py: type a question, get a grounded
answer plus the source documents it was retrieved from.

    python app.py
    # then open http://localhost:7860
"""

import gradio as gr

from query import ask


def handle_query(question):
    result = ask(question)
    if result["sources"]:
        sources = "\n".join(f"• {s}" for s in result["sources"])
    else:
        sources = "(no sources — outside the corpus)"
    return result["answer"], sources


with gr.Blocks() as demo:
    gr.Markdown("# The Unofficial Guide\nAsk about UC Berkeley CS courses & professors. "
                "Answers come only from real student reviews and Reddit threads.")
    inp = gr.Textbox(label="Your question")
    btn = gr.Button("Ask")
    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Textbox(label="Retrieved from", lines=4)
    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])

demo.launch()
