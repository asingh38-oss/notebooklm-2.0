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

NotebookLM 2.0 is an AI-powered research assistant built with Gradio, OpenAI, and ChromaDB. It lets users organize sources into notebooks, chat with grounded answers, and generate study artifacts like reports, quizzes, and podcast-style summaries.

## Live Demo

- GitHub Repo: [asingh38-oss/notebooklm-2.0](https://github.com/asingh38-oss/notebooklm-2.0)
- Hugging Face Space: [NotebookLM 2.0 on Hugging Face](https://huggingface.co/spaces/asingh38-oss/notebooklm-2.0)

## Features

- Multi-notebook workspace for separate courses, projects, or study topics
- Source ingestion from PDF, PPTX, TXT, Markdown, and web URLs
- Retrieval-augmented chat grounded in indexed notebook sources
- ChromaDB-backed local persistence for notebook-specific document retrieval
- One-click artifacts for reports, quizzes, and podcast transcripts
- Optional podcast audio generation with OpenAI text-to-speech
- Lightweight login system powered by environment variables
- Hugging Face Spaces-ready Gradio app entry point

## Tech Stack

- Frontend: Gradio
- LLM + embeddings + TTS: OpenAI API
- Vector store: ChromaDB
- Parsing: `pdfplumber`, `python-pptx`, `trafilatura`
- Config: `python-dotenv`

## Environment Variables

Set these in a local `.env` file or in Hugging Face Space secrets.

| Variable | Required | Example | Purpose |
|---|---|---|---|
| `OPENAI_API_KEY` | Yes | `sk-...` | Used for chat, embeddings, artifact generation, and podcast audio |
| `USERS` | Yes | `demo:demo,alice:pass123` | Login credentials for the app |
| `CHUNK_SIZE` | No | `800` | Character window size used during ingestion |
| `CHUNK_OVERLAP` | No | `150` | Overlap between adjacent chunks |
| `EMBED_MODEL` | No | `text-embedding-3-small` | Embedding model used for Chroma indexing |
| `OPENAI_MODEL` | No | `gpt-4o` | Model used for report, quiz, and podcast transcript generation |
| `OPENAI_PODCAST_VOICE` | No | `alloy` | Voice for generated podcast audio |

## Hugging Face Spaces Setup

This project is configured for a Gradio Space through the metadata block at the top of this README.

Add these in your Space under `Settings -> Repository secrets`:

| Secret | Required | Notes |
|---|---|---|
| `OPENAI_API_KEY` | Yes | Needed for chat, embeddings, artifacts, and TTS |
| `USERS` | Yes | Format: `alice:pass1,bob:pass2` |
| `CHUNK_SIZE` | No | Optional tuning override |
| `CHUNK_OVERLAP` | No | Optional tuning override |
| `EMBED_MODEL` | No | Defaults to `text-embedding-3-small` |
| `OPENAI_MODEL` | No | Defaults to `gpt-4o` |
| `OPENAI_PODCAST_VOICE` | No | Defaults to `alloy` |

Deployment notes:

- The Space entrypoint is [`app.py`](/Users/darellsam/Desktop/NotebookLM 2.0/notebooklm-2.0/app.py).
- User notebooks and indexed data are stored under `data/users/` at runtime.
- If the Space restarts, only files persisted by the Space storage layer remain available.
- The first ingestion request may be slower because embeddings and vector collections are created on demand.

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
