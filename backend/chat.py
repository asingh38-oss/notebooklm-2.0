import os

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from openai import OpenAI

from backend.storage import get_chroma_path


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
CHAT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

client = OpenAI()


def _embedding_fn():
    return OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY,
        model_name=EMBED_MODEL,
    )


def _retrieve_chunks(username: str, nb_id: str, query: str, top_k: int = 5) -> tuple[list[str], list[dict]]:
    chroma_path = get_chroma_path(username, nb_id)
    collection = chromadb.PersistentClient(path=chroma_path).get_or_create_collection(
        name="sources",
        embedding_function=_embedding_fn(),
        metadata={"hnsw:space": "cosine"},
    )

    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        include=["documents", "metadatas"],
    )

    documents = (results.get("documents") or [[]])[0]
    metadatas = (results.get("metadatas") or [[]])[0]
    return documents, metadatas


def _format_history(history: list) -> list:
    return [
        {"role": msg["role"], "content": msg["content"]}
        for msg in history
        if msg.get("content")
    ]


def chat_with_sources(message: str, nb_id: str, username: str, history: list) -> str:
    try:
        chunks, metas = _retrieve_chunks(username, nb_id, message, top_k=5)

        if not chunks:
            return (
                "I couldn't find any indexed source content for this notebook yet. "
                "Upload a file or add a URL in the Sources tab first."
            )

        context_parts = []
        for chunk, meta in zip(chunks, metas):
            source = meta.get("source", "unknown")
            chunk_idx = meta.get("chunk_index", "?")
            context_parts.append(f"[Source: {source} | Chunk: {chunk_idx}]\n{chunk}")
        context = "\n\n---\n\n".join(context_parts)

        system_prompt = (
            "You are a helpful research assistant. "
            "Answer the user's question using only the retrieved notebook context below. "
            "Cite supporting evidence inline in this format: [Source: filename | Chunk: N]. "
            "If the context is insufficient, say so clearly.\n\n"
            f"Context:\n{context}"
        )

        messages = [{"role": "system", "content": system_prompt}]
        messages += _format_history(history)
        messages.append({"role": "user", "content": message})

        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            temperature=0.3,
        )
        answer = response.choices[0].message.content or ""

        seen = set()
        source_lines = []
        for meta in metas:
            src = meta.get("source", "unknown")
            if src not in seen and src not in ("none", "error"):
                seen.add(src)
                source_lines.append(f"- {src}")

        if source_lines:
            answer += "\n\nSources consulted:\n" + "\n".join(source_lines)

        return answer
    except Exception as e:
        return f"Could not generate a response from notebook sources: {e}"
