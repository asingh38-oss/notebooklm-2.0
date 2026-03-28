from openai import OpenAI
from backend.retrieval import get_retriever

client = OpenAI()

def _format_history(history: list) -> list:
    return [
        {"role": msg["role"], "content": msg["content"]}
        for msg in history if msg.get("content")
    ]

def chat_with_sources(message: str, nb_id: str, username: str, history: list) -> str:
    try:
        retrieve = get_retriever(nb_id, username=username, top_k=5)
        chunks, metas = retrieve(message)

        context_parts = []
        for chunk, meta in zip(chunks, metas):
            source = meta.get("source", "unknown")
            chunk_idx = meta.get("chunk_index", meta.get("chunk", "?"))
            context_parts.append(f"[Source: {source} | Chunk: {chunk_idx}]\n{chunk}")
        context = "\n\n---\n\n".join(context_parts)

        system_prompt = (
            "You are a helpful research assistant. "
            "Answer the user's question using ONLY the context provided below. "
            "After each claim, cite the source inline: [Source: filename | Chunk: N]. "
            "If the context does not contain enough information, say so.\n\n"
            f"Context:\n{context}"
        )

        messages = [{"role": "system", "content": system_prompt}]
        messages += _format_history(history)
        messages.append({"role": "user", "content": message})

        response = client.chat.completions.create(
            model="gpt-4o", messages=messages, temperature=0.3,
        )
        answer = response.choices[0].message.content or ""

        seen, source_lines = set(), []
        for meta in metas:
            src = meta.get("source", "unknown")
            if src not in seen and src not in ("none", "error"):
                seen.add(src)
                source_lines.append(f"- `{src}`")

        if source_lines:
            answer += "\n\n**Sources consulted:**\n" + "\n".join(source_lines)

        return answer

    except Exception as e:
        return f"Error generating response: {e}"