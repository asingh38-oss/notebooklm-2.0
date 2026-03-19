---
title: NotebookLM 2.0
emoji: 📓
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: "5.0.0"
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
```bash
