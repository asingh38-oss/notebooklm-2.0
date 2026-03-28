---
title: NotebookLM 2.0
emoji: 📓
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: 5.23.0
app_file: app.py
pinned: false
---

# NotebookLM 2.0

An AI-powered research assistant. Upload documents, chat with your sources,
and generate study reports, quizzes, and podcasts — powered by GPT-4o and
ChromaDB RAG with recursive chunking.

## Features

- **Multi-notebook workspace** — create and manage separate notebooks per topic
- **Source ingestion** — upload PDF, PPTX, TXT, or paste a URL
- **RAG chat** — GPT-4o answers grounded in your sources with inline citations
- **Artifacts** — one-click study report, quiz, and podcast (transcript + audio)
- **Login system** — simple username/password auth via environment variable

## Hugging Face Spaces Setup

Set these in your Space → **Settings → Repository secrets**:

| Secret           | Description                                          |
|------------------|------------------------------------------------------|
| `OPENAI_API_KEY` | Your OpenAI API key                                  |
| `USERS`          | Comma-separated credentials: `alice:pass1,bob:pass2` |

## Local Setup

1. Clone the repository:

```bash
git clone https://github.com/your-org/notebooklm-2.0.git
cd notebooklm-2.0
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file at the project root and set your environment variables.

5. Start the app locally:

```bash
python app.py
```

The app will launch a local Gradio interface. Open the printed URL in your browser.

## Environment Variables

| Name                  | Required | Default                  | Description |
|-----------------------|----------|--------------------------|-------------|
| `OPENAI_API_KEY`      | yes      | n/a                      | OpenAI API key for embeddings, chat, and artifact generation |
| `USERS`               | yes      | `demo:demo`              | Comma-separated login credentials in `user:pass` format |
| `OPENAI_MODEL`        | no       | `gpt-4o`                 | OpenAI model used for artifact generation |
| `OPENAI_PODCAST_VOICE`| no       | `alloy`                  | Voice for podcast text-to-speech generation |
| `CHUNK_SIZE`          | no       | `800`                    | Document chunk size for embedding ingestion |
| `CHUNK_OVERLAP`       | no       | `150`                    | Token overlap between ingestion chunks |
| `EMBED_MODEL`         | no       | `text-embedding-3-small` | OpenAI embedding model used by ChromaDB |

Example `.env` contents:

```env
OPENAI_API_KEY=sk-...
USERS=alice:pass1,bob:pass2
OPENAI_MODEL=gpt-4o
OPENAI_PODCAST_VOICE=alloy
CHUNK_SIZE=800
CHUNK_OVERLAP=150
EMBED_MODEL=text-embedding-3-small
```

## Project Structure

- `app.py` — Gradio frontend and login workflow.
- `requirements.txt` — Python dependencies.
- `backend/` — backend application logic:
  - `artifacts.py` — generate reports, quizzes, and podcasts from notebook content.
  - `chat.py` — RAG chat interface for notebook sources.
  - `ingestion.py` — extract, chunk, embed, and store documents into ChromaDB.
  - `retrieval.py` — retrieval utilities and vector database helpers.
  - `storage.py` — notebook and user persistence helpers.

## Usage Guide

1. Open the app in your browser.
2. Login with one of the credentials configured in `USERS`.
3. Create a new notebook for your topic.
4. Upload source documents or paste a URL in the Sources tab.
5. Ask questions in the Chat tab; answers are grounded in your uploaded sources.
6. Use the Artifacts tab to generate:
   - study reports
   - quizzes
   - podcasts (transcript + audio)

## Hugging Face Space

Live demo: https://huggingface.co/spaces/asingh38/notebooklm-2.0

## Notes

- The app uses local `data/` storage for notebooks, source text, and ChromaDB persistence.
- If `USERS` is not set, the app defaults to `demo:demo` for a quick local trial.
- For production deployments, keep your `OPENAI_API_KEY` secret and avoid committing `.env` to version control.
