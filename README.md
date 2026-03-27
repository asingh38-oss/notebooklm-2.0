---
title: NotebookLM 2.0
emoji: 📓
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: "4.42.0"
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
git clone https://github.com/asingh38-oss/notebooklm-2.0.git
cd notebooklm-2.0
```

2. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file from the example:

```bash
cp .env.example .env
```

5. Fill in at least:

```env
OPENAI_API_KEY=your_openai_key_here
USERS=demo:demo
```

6. Start the app:

```bash
python3 app.py
```

7. Open the local Gradio URL printed in the terminal, then sign in with one of the `USERS` credentials.

## Usage Guide

### 1. Sign in

Use a username and password from the `USERS` environment variable.

### 2. Create a notebook

Enter a notebook name in the top bar and click `Create`.

### 3. Add sources

You can:

- Upload PDF, PPTX, or TXT files
- Paste a URL for web ingestion

Each source is extracted, chunked, embedded, and stored in a Chroma collection scoped to that notebook.

### 4. Chat with your sources

Open the `Chat` tab and ask questions about the indexed material. Responses are generated with notebook-specific retrieved context and source citations.

### 5. Generate artifacts

Open the `Artifacts` tab to generate:

- Study report
- Multiple-choice quiz
- Podcast transcript
- Optional podcast audio when TTS succeeds

## Project Structure

```text
notebooklm-2.0/
├── app.py
├── requirements.txt
├── .env.example
├── backend/
│   ├── __init__.py
│   ├── artifacts.py
│   ├── chat.py
│   ├── ingestion.py
│   ├── retrieval.py
│   └── storage.py
└── data/
    └── users/
```

File overview:

- [`app.py`](/Users/darellsam/Desktop/NotebookLM 2.0/notebooklm-2.0/app.py): Gradio UI and app entrypoint for local runs and HF Spaces
- [`backend/storage.py`](/Users/darellsam/Desktop/NotebookLM 2.0/notebooklm-2.0/backend/storage.py): notebook, artifact, and chat persistence helpers
- [`backend/ingestion.py`](/Users/darellsam/Desktop/NotebookLM 2.0/notebooklm-2.0/backend/ingestion.py): extraction, chunking, embedding, and Chroma indexing
- [`backend/chat.py`](/Users/darellsam/Desktop/NotebookLM 2.0/notebooklm-2.0/backend/chat.py): retrieval-grounded notebook chat
- [`backend/artifacts.py`](/Users/darellsam/Desktop/NotebookLM 2.0/notebooklm-2.0/backend/artifacts.py): report, quiz, and podcast generation
- [`backend/retrieval.py`](/Users/darellsam/Desktop/NotebookLM 2.0/notebooklm-2.0/backend/retrieval.py): advanced retrieval utilities for the project RAG work

## Data Storage

Per-user notebook data is stored like this:

```text
data/users/<username>/notebooks/
├── index.json
└── <notebook-id>/
    ├── artifacts/
    ├── chat/
    ├── chroma/
    ├── files_extracted/
    └── files_raw/
```

This keeps notebooks isolated by user and allows each notebook to maintain its own vector store.

## Notes for Evaluators

- Default chunking strategy is recursive chunking
- Retrieval is notebook-scoped, so only the active notebook's indexed sources are searched
- Artifact generation uses OpenAI directly and saves outputs back into the notebook directory
- The app uses lazy backend imports to reduce cold-start failures on Hugging Face Spaces

## Troubleshooting

- `Invalid username or password`: confirm the `USERS` secret uses `username:password` pairs separated by commas
- `OPENAI_API_KEY not set`: add the key locally in `.env` or in Space secrets
- Ingestion fails for URLs: some sites block scraping or do not expose enough readable text
- No answers from chat: make sure you created a notebook and ingested at least one source first
- Podcast audio missing: transcript generation succeeded, but TTS may have failed or been unavailable

## License

This repository is intended for academic project use unless your team adds a separate license file.
