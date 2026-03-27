"""
app.py — NotebookLM 2.0
Gradio frontend / Hugging Face Spaces entry point.

Screens:
  1. Login  — username + password (configured via USERS env var)
  2. Main   — Notebook selector, then three tabs:
              💬 Chat | 📂 Sources | ✨ Artifacts
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import gradio as gr

from backend.persistence import pull_data, push_data

load_dotenv()

# Pull persisted data from HF Dataset on startup
pull_data()


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def _parse_users() -> dict[str, str]:
    """
    Parse USERS env var into {username: password}.
    Format: "alice:pass1,bob:pass2"
    Falls back to demo:demo if not set.
    """
    raw = os.getenv("USERS", "demo:demo")
    users = {}
    for pair in raw.split(","):
        pair = pair.strip()
        if ":" in pair:
            u, p = pair.split(":", 1)
            users[u.strip()] = p.strip()
    return users

USERS = _parse_users()


def login(username: str, password: str) -> tuple[bool, str]:
    """Return (success, username_or_error_message)."""
    if not username or not password:
        return False, "Please enter both username and password."
    if USERS.get(username) == password:
        return True, username
    return False, "Invalid username or password."


# ---------------------------------------------------------------------------
# Backend (lazy import so HF Spaces cold-start doesn't fail on missing keys)
# ---------------------------------------------------------------------------

def _be():
    """Return dict of backend callables."""
    from backend.storage import (
        get_user_notebooks,
        create_notebook_for_user,
        delete_notebook,
    )
    from backend.ingestion import ingest_source, list_indexed_sources
    from backend.chat import chat_with_sources
    from backend.artifacts import generate_report, generate_quiz, generate_podcast
    return {
        "get_notebooks":   get_user_notebooks,
        "create_notebook": create_notebook_for_user,
        "delete_notebook": delete_notebook,
        "list_sources":    list_indexed_sources,
        "ingest":          ingest_source,
        "chat":            chat_with_sources,
        "report":          generate_report,
        "quiz":            generate_quiz,
        "podcast":         generate_podcast,
    }


# ---------------------------------------------------------------------------
# Notebook dropdown helpers
# ---------------------------------------------------------------------------

def _nb_choices(username: str) -> list[str]:
    """Return list of 'Notebook Name  [uuid]' strings for the dropdown."""
    nbs = _be()["get_notebooks"](username)
    return [f"{nb['name']}  [{nb['id']}]" for nb in nbs]


def _parse_choice(choice: str) -> tuple[str, str]:
    """Extract (name, nb_id) from a dropdown choice string."""
    if not choice:
        return "", ""
    name, _, rest = choice.rpartition("  [")
    return name.strip(), rest.rstrip("]").strip()


def _sources_md(username: str, nb_id: str) -> str:
    """Return a Markdown list of indexed source names for a notebook."""
    if not username or not nb_id:
        return "_No notebook selected._"
    try:
        sources = _be()["list_sources"](username, nb_id)
        if not sources:
            return "_No sources indexed yet. Upload files or add a URL in the Sources tab._"
        return "\n".join(f"- `{s}`" for s in sources)
    except Exception as e:
        return f"_Could not load sources: {e}_"


# ---------------------------------------------------------------------------
# CSS — dark editorial theme
# ---------------------------------------------------------------------------

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=JetBrains+Mono:wght@300;400;500&display=swap');

:root {
    --bg:         #0a0a0f;
    --bg2:        #111118;
    --bg3:        #16161f;
    --bg4:        #1c1c28;
    --accent:     #7c6af7;
    --accent2:    #9d8fff;
    --glow:       rgba(124,106,247,0.15);
    --text:       #e8e6f0;
    --text2:      #8b87a8;
    --muted:      #504d6e;
    --border:     #2a2840;
    --border2:    #3d3960;
    --ok:         #5af0a0;
    --warn:       #f0c45a;
    --err:        #f05a7a;
    --r:          10px;
    --mono:       'JetBrains Mono', 'Fira Code', monospace;
    --display:    'Playfair Display', Georgia, serif;
}

*, *::before, *::after { box-sizing: border-box; }

body, .gradio-container {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: var(--mono) !important;
}

#login-wrap {
    max-width: 420px;
    margin: 72px auto 0;
    padding: 48px 40px 40px;
    background: var(--bg3);
    border: 1px solid var(--border);
    border-radius: 18px;
    box-shadow: 0 0 80px var(--glow);
}
#login-title {
    font-family: var(--display);
    font-size: 2rem;
    font-weight: 700;
    text-align: center;
    margin-bottom: 4px;
    color: var(--text);
    letter-spacing: -0.5px;
}
#login-sub {
    font-size: 0.72rem;
    color: var(--muted);
    text-align: center;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 36px;
}

#hdr {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 28px;
    background: var(--bg2);
    border-bottom: 1px solid var(--border);
}
#hdr-title {
    font-family: var(--display);
    font-size: 1.35rem;
    color: var(--text);
}
#hdr-title span { color: var(--accent2); }

#nb-bar {
    display: flex;
    gap: 10px;
    align-items: flex-end;
    padding: 12px 20px;
    background: var(--bg2);
    border-bottom: 1px solid var(--border);
}

.gr-button, button {
    font-family: var(--mono) !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em !important;
    border-radius: var(--r) !important;
    transition: all 0.18s ease !important;
}
.gr-button-primary {
    background: var(--accent) !important;
    color: #fff !important;
    border: none !important;
}
.gr-button-primary:hover {
    background: var(--accent2) !important;
    box-shadow: 0 0 18px var(--glow) !important;
    transform: translateY(-1px) !important;
}
.gr-button-stop {
    background: transparent !important;
    color: var(--err) !important;
    border: 1px solid var(--err) !important;
}

input, textarea, .gr-textbox textarea {
    background: var(--bg4) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r) !important;
    color: var(--text) !important;
    font-family: var(--mono) !important;
    font-size: 0.85rem !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
input:focus, textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--glow) !important;
    outline: none !important;
}

label, .gr-block-label {
    color: var(--text2) !important;
    font-family: var(--mono) !important;
    font-size: 0.72rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}

.tab-nav button {
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    color: var(--text2) !important;
    font-family: var(--mono) !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    padding: 12px 20px !important;
    transition: all 0.2s !important;
}
.tab-nav button.selected {
    color: var(--accent2) !important;
    border-bottom-color: var(--accent) !important;
}

.chatbot {
    background: var(--bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r) !important;
}

.gr-markdown {
    background: var(--bg3) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r) !important;
    padding: 20px !important;
    font-family: var(--mono) !important;
    font-size: 0.84rem !important;
    line-height: 1.75 !important;
    color: var(--text) !important;
}
.gr-markdown h1, .gr-markdown h2, .gr-markdown h3 {
    font-family: var(--display) !important;
    color: var(--text) !important;
}

select, .gr-dropdown select {
    background: var(--bg4) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    font-family: var(--mono) !important;
    border-radius: var(--r) !important;
}

.gr-accordion {
    background: var(--bg3) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r) !important;
    margin-bottom: 8px !important;
}

.ok   { color: var(--ok)   !important; }
.warn { color: var(--warn) !important; }
.err  { color: var(--err)  !important; }

.gr-file-upload {
    background: var(--bg3) !important;
    border: 1px dashed var(--border2) !important;
    border-radius: var(--r) !important;
}

::-webkit-scrollbar            { width: 5px; height: 5px; }
::-webkit-scrollbar-track      { background: var(--bg); }
::-webkit-scrollbar-thumb      { background: var(--border2); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover{ background: var(--accent); }

audio { width: 100%; border-radius: var(--r); }
"""


# ---------------------------------------------------------------------------
# Build UI
# ---------------------------------------------------------------------------

def build_ui() -> gr.Blocks:

    with gr.Blocks(title="NotebookLM 2.0") as demo:

        # ── Persistent state ───────────────────────────────────────────────
        s_user  = gr.State("")
        s_nb_id = gr.State("")

        # ==================================================================
        # LOGIN SCREEN
        # ==================================================================
        with gr.Column(elem_id="login-wrap", visible=True) as screen_login:
            gr.HTML('<div id="login-title">NotebookLM 2.0</div>')
            gr.HTML('<div id="login-sub">AI Research Assistant</div>')
            inp_user  = gr.Textbox(label="Username", placeholder="username")
            inp_pass  = gr.Textbox(label="Password", placeholder="password", type="password")
            btn_login = gr.Button("Sign In", variant="primary")
            msg_login = gr.Markdown("")

        # ==================================================================
        # MAIN APP
        # ==================================================================
        with gr.Column(visible=False) as screen_main:

            # Header
            with gr.Row(elem_id="hdr"):
                gr.HTML('<div id="hdr-title">Notebook<span>LM</span> 2.0</div>')
                lbl_user = gr.Markdown("", elem_classes=["ok"])

            # Notebook bar
            with gr.Row(elem_id="nb-bar"):
                dd_nb       = gr.Dropdown(choices=[], label="Active Notebook", scale=4, interactive=True)
                inp_nb_name = gr.Textbox(placeholder="New notebook name…", label="", scale=3, show_label=False)
                btn_create  = gr.Button("＋ Create", scale=1, variant="primary")
                btn_delete  = gr.Button("✕ Delete",  scale=1, variant="stop")

            md_nb_status = gr.Markdown("")

            # ── Tabs ───────────────────────────────────────────────────────
            with gr.Tabs():

                # TAB 1 — CHAT
                with gr.TabItem("💬  Chat"):
                    chatbot = gr.Chatbot(
                        label="",
                        height=460,
                        show_label=False,
                        bubble_full_width=False,
                    )
                    with gr.Row():
                        inp_chat = gr.Textbox(
                            placeholder="Ask anything about your sources…",
                            label="", show_label=False, scale=5, lines=1,
                        )
                        btn_send = gr.Button("Send →", scale=1, variant="primary")
                    btn_clear = gr.Button("Clear chat", size="sm")

                # TAB 2 — SOURCES
                with gr.TabItem("📂  Sources"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            gr.Markdown("### Upload Files")
                            inp_files  = gr.File(
                                label="PDF / PPTX / TXT",
                                file_types=[".pdf", ".pptx", ".txt"],
                                file_count="multiple",
                            )
                            btn_upload = gr.Button("Ingest Files", variant="primary")
                        with gr.Column(scale=1):
                            gr.Markdown("### Add URL")
                            inp_url = gr.Textbox(label="Web URL", placeholder="https://…")
                            btn_url = gr.Button("Ingest URL", variant="primary")

                    md_ingest = gr.Markdown("")
                    gr.Markdown("---")
                    gr.Markdown("### Indexed Sources")
                    md_sources  = gr.Markdown("_No sources indexed yet._")
                    btn_refresh = gr.Button("↻ Refresh", size="sm")

                # TAB 3 — ARTIFACTS
                with gr.TabItem("✨  Artifacts"):
                    with gr.Row():
                        btn_report  = gr.Button("📄  Generate Report",  variant="primary", scale=1)
                        btn_quiz    = gr.Button("❓  Generate Quiz",    variant="primary", scale=1)
                        btn_podcast = gr.Button("🎙️  Generate Podcast", variant="primary", scale=1)

                    md_art_status = gr.Markdown("")

                    with gr.Accordion("📄  Report", open=False):
                        md_report = gr.Markdown("")
                    with gr.Accordion("❓  Quiz", open=False):
                        md_quiz = gr.Markdown("")
                    with gr.Accordion("🎙️  Podcast", open=False):
                        md_transcript = gr.Markdown("")
                        aud_podcast   = gr.Audio(label="Listen", visible=False)

        # ==================================================================
        # EVENT HANDLERS
        # ==================================================================

        # ── Login ──────────────────────────────────────────────────────────
        def do_login(username, password):
            ok, result = login(username, password)
            if ok:
                choices = _nb_choices(result)
                return (
                    gr.update(visible=False),
                    gr.update(visible=True),
                    result,
                    gr.update(choices=choices, value=choices[0] if choices else None),
                    f"✦ **{result}**",
                    "",
                )
            return (
                gr.update(visible=True),
                gr.update(visible=False),
                "", gr.update(), "",
                f"⚠ {result}",
            )

        for trigger in [btn_login.click, inp_pass.submit]:
            trigger(
                do_login,
                inputs=[inp_user, inp_pass],
                outputs=[screen_login, screen_main, s_user, dd_nb, lbl_user, msg_login],
            )

        # ── Notebook selection ─────────────────────────────────────────────
        def on_nb_select(choice):
            _, nb_id = _parse_choice(choice)
            return nb_id

        dd_nb.change(on_nb_select, inputs=[dd_nb], outputs=[s_nb_id])

        # ── Create notebook ────────────────────────────────────────────────
        def do_create(username, name):
            if not name.strip():
                return gr.update(), "", "⚠ Enter a notebook name."
            if not username:
                return gr.update(), "", "⚠ Not signed in."
            _be()["create_notebook"](username, name.strip())
            push_data()
            choices = _nb_choices(username)
            return gr.update(choices=choices, value=choices[-1]), "", f"✦ Created **{name.strip()}**"

        btn_create.click(
            do_create,
            inputs=[s_user, inp_nb_name],
            outputs=[dd_nb, inp_nb_name, md_nb_status],
        )

        # ── Delete notebook ────────────────────────────────────────────────
        def do_delete(username, nb_id):
            if not nb_id:
                return gr.update(), "⚠ No notebook selected."
            _be()["delete_notebook"](username, nb_id)
            push_data()
            choices = _nb_choices(username)
            return gr.update(choices=choices, value=choices[0] if choices else None), "✦ Deleted."

        btn_delete.click(do_delete, inputs=[s_user, s_nb_id], outputs=[dd_nb, md_nb_status])

        # ── Chat ───────────────────────────────────────────────────────────
        def do_chat(message, nb_id, username, history):
            if not message.strip():
                return history, ""
            if not nb_id:
                history = (history or []) + [{"role": "assistant", "content": "⚠ Select a notebook first."}]
                return history, ""
            history = list(history or [])
            history.append({"role": "user", "content": message})
            reply = _be()["chat"](message, nb_id, username, history[:-1])
            history.append({"role": "assistant", "content": reply})
            return history, ""

        btn_send.click(do_chat, inputs=[inp_chat, s_nb_id, s_user, chatbot], outputs=[chatbot, inp_chat])
        inp_chat.submit(do_chat, inputs=[inp_chat, s_nb_id, s_user, chatbot], outputs=[chatbot, inp_chat])
        btn_clear.click(lambda: [], outputs=[chatbot])

        # ── Ingest files ───────────────────────────────────────────────────
        def do_upload(files, nb_id, username):
            if not nb_id:
                return "⚠ Select a notebook first.", _sources_md(username, nb_id)
            if not files:
                return "⚠ No files selected.", _sources_md(username, nb_id)
            msgs = []
            for f in files:
                path = f.name if hasattr(f, "name") else str(f)
                raw  = Path(path).read_bytes()
                try:
                    res = _be()["ingest"](username, nb_id, path, raw_bytes=raw)
                    msgs.append(f"✦ **{res['source_name']}** — {res['chunk_count']} chunks ({res['strategy']})")
                except Exception as e:
                    msgs.append(f"✕ {e}")
            push_data()
            return "\n\n".join(msgs), _sources_md(username, nb_id)

        btn_upload.click(do_upload, inputs=[inp_files, s_nb_id, s_user], outputs=[md_ingest, md_sources])

        # ── Ingest URL ─────────────────────────────────────────────────────
        def do_url(url, nb_id, username):
            if not nb_id:
                return "⚠ Select a notebook first.", _sources_md(username, nb_id)
            if not url.strip():
                return "⚠ Enter a URL.", _sources_md(username, nb_id)
            try:
                res = _be()["ingest"](username, nb_id, url.strip())
                msg = f"✦ **{res['source_name']}** — {res['chunk_count']} chunks ({res['strategy']})"
            except Exception as e:
                msg = f"✕ {e}"
            push_data()
            return msg, _sources_md(username, nb_id)

        btn_url.click(do_url, inputs=[inp_url, s_nb_id, s_user], outputs=[md_ingest, md_sources])

        # ── Refresh sources ────────────────────────────────────────────────
        btn_refresh.click(
            lambda u, n: _sources_md(u, n),
            inputs=[s_user, s_nb_id],
            outputs=[md_sources],
        )

        # ── Report ─────────────────────────────────────────────────────────
        def do_report(nb_id, username):
            if not nb_id:
                return "⚠ Select a notebook first.", ""
            return "✦ Report generated.", _be()["report"](nb_id, username)

        btn_report.click(do_report, inputs=[s_nb_id, s_user], outputs=[md_art_status, md_report])

        # ── Quiz ───────────────────────────────────────────────────────────
        def do_quiz(nb_id, username):
            if not nb_id:
                return "⚠ Select a notebook first.", ""
            return "✦ Quiz generated.", _be()["quiz"](nb_id, username)

        btn_quiz.click(do_quiz, inputs=[s_nb_id, s_user], outputs=[md_art_status, md_quiz])

        # ── Podcast ────────────────────────────────────────────────────────
        def do_podcast(nb_id, username):
            if not nb_id:
                return "⚠ Select a notebook first.", "", gr.update(visible=False)
            transcript, audio_path = _be()["podcast"](nb_id, username)
            audio_update = gr.update(value=audio_path, visible=True) if audio_path else gr.update(visible=False)
            return "✦ Podcast generated.", transcript, audio_update

        btn_podcast.click(
            do_podcast,
            inputs=[s_nb_id, s_user],
            outputs=[md_art_status, md_transcript, aud_podcast],
        )

    return demo


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    demo = build_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        css=CSS,
        theme=gr.themes.Base(),
    )