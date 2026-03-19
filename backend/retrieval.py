import os
import chromadb
from openai import OpenAI
from backend.storage import notebook_dir

client = OpenAI()

def _embed(text: str) -> list[float]:
    response = client.embeddings.create(
        model=os.getenv("EMBED_MODEL", "text-embedding-3-small"),
        input=[text],
    )
    return response.data[0].embedding

def get_retriever(nb_id: str, username: str = "default", top_k: int = 5):
    def retrieve(query: str) -> tuple[list[str], list[dict]]:
        try:
            chroma_path = str(notebook_dir(username, nb_id) / "chroma")
            chroma_client = chromadb.PersistentClient(path=chroma_path)
            collection = chroma_client.get_or_create_collection(
                name="sources",
                metadata={"hnsw:space": "cosine"},
            )

            if collection.count() == 0:
                return (
                    ["No sources have been ingested yet."],
                    [{"source": "none", "chunk_index": 0}],
                )

            query_embedding = _embed(query)
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, collection.count()),
            )
            return results["documents"][0], results["metadatas"][0]

        except Exception as e:
            return (
                [f"Retrieval error: {e}"],
                [{"source": "error", "chunk_index": 0}],
            )

    return retrieve