"""
retrieval.py

Retrieval layer for the local RAG MCP server.

Features:
- Load a persisted Chroma vector database
- Basic similarity retrieval
- Fusion Retrieval (multiple generated search queries)
- HyDE (Hypothetical Document Embeddings)
- Result deduplication
- Formatting chunks for MCP tool responses

Example usage:
    retriever = DocumentationRetriever(
        persist_directory="./chroma_db",
        embedding_model=embeddings,
        llm=my_llm,
        strategy="fusion",
    )

    results = retriever.retrieve("How do I build a LangChain retriever with Chroma?")
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Sequence, Tuple

from langchain_chroma import Chroma
from langchain_core.documents import Document


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class RetrievedChunk:
    """A normalized chunk returned from the vector store."""
    content: str
    source: str = "unknown"
    score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Main retriever
# ---------------------------------------------------------------------------

class DocumentationRetriever:
    """
    Documentation retriever for the local RAG server.

    Parameters
    ----------
    persist_directory:
        Path to the Chroma persisted database.
    embedding_model:
        LangChain embedding model instance.
    llm:
        Optional LLM instance used for query expansion / HyDE.
    collection_name:
        Name of the Chroma collection.
    strategy:
        Retrieval strategy. One of:
            - "basic"
            - "fusion"
            - "hyde"
    k:
        Number of results to return after reranking / dedupe.
    fetch_k:
        Number of raw documents to fetch from the vector store.
    """

    def __init__(
        self,
        persist_directory: str,
        embedding_model: Any,
        llm: Optional[Any] = None,
        collection_name: str = "docs",
        strategy: str = "basic",
        k: int = 5,
        fetch_k: int = 10,
    ) -> None:
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model
        self.llm = llm
        self.collection_name = collection_name
        self.strategy = strategy.lower()
        self.k = k
        self.fetch_k = fetch_k

        self.vectorstore = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embedding_model,
            persist_directory=self.persist_directory,
        )

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def retrieve(self, query: str) -> List[RetrievedChunk]:
        """
        Main retrieval entry point.

        Depending on the configured strategy, this will do:
        - basic similarity search
        - fusion retrieval
        - HyDE retrieval
        """
        strategy = self.strategy

        if strategy == "basic":
            return self._basic_retrieval(query)
        if strategy == "fusion":
            return self._fusion_retrieval(query)
        if strategy == "hyde":
            return self._hyde_retrieval(query)

        raise ValueError(
            f"Unsupported retrieval strategy: {strategy}. "
            f"Choose from 'basic', 'fusion', or 'hyde'."
        )

    def retrieve_as_text(self, query: str) -> str:
        """
        Retrieve chunks and format them as a compact text block for the agent.
        Useful when sending results back to the MCP client / LLM context.
        """
        chunks = self.retrieve(query)
        if not chunks:
            return "No relevant documentation chunks found."

        formatted_blocks: List[str] = []
        for i, chunk in enumerate(chunks, start=1):
            source = chunk.source or "unknown"
            score_str = f"{chunk.score:.4f}" if chunk.score is not None else "n/a"
            formatted_blocks.append(
                f"[Chunk {i}]\n"
                f"Source: {source}\n"
                f"Score: {score_str}\n"
                f"Content:\n{chunk.content}"
            )

        return "\n\n".join(formatted_blocks)

    def retrieve_as_dicts(self, query: str) -> List[Dict[str, Any]]:
        """Retrieve chunks and return them as serializable dicts."""
        return [chunk.to_dict() for chunk in self.retrieve(query)]

    # -----------------------------------------------------------------------
    # Retrieval strategies
    # -----------------------------------------------------------------------

    def _basic_retrieval(self, query: str) -> List[RetrievedChunk]:
        """Plain similarity search."""
        docs_and_scores = self._similarity_search_with_scores(query, k=self.fetch_k)
        return self._normalize_and_trim(docs_and_scores, final_k=self.k)

    def _fusion_retrieval(self, query: str) -> List[RetrievedChunk]:
        """
        Fusion Retrieval:
        1. Generate multiple related search queries
        2. Retrieve docs for each query
        3. Merge and deduplicate
        """
        expanded_queries = self._generate_fusion_queries(query)
        all_results: List[Tuple[Document, Optional[float]]] = []

        for expanded_query in expanded_queries:
            docs_and_scores = self._similarity_search_with_scores(
                expanded_query,
                k=self.fetch_k,
            )
            all_results.extend(docs_and_scores)

        return self._normalize_and_trim(all_results, final_k=self.k)

    def _hyde_retrieval(self, query: str) -> List[RetrievedChunk]:
        """
        HyDE retrieval:
        1. Ask the LLM to generate a hypothetical ideal answer/document
        2. Use that generated text as the retrieval query
        """
        hypothetical_doc = self._generate_hypothetical_document(query)
        docs_and_scores = self._similarity_search_with_scores(
            hypothetical_doc,
            k=self.fetch_k,
        )
        return self._normalize_and_trim(docs_and_scores, final_k=self.k)

    # -----------------------------------------------------------------------
    # Vector search helpers
    # -----------------------------------------------------------------------

    def _similarity_search_with_scores(
        self,
        query: str,
        k: int,
    ) -> List[Tuple[Document, Optional[float]]]:
        """
        Run similarity search with scores when available.

        Chroma usually returns lower scores for closer matches depending on config,
        but score meaning can vary by backend. For this project, we display score
        without over-claiming a universal interpretation.
        """
        try:
            return self.vectorstore.similarity_search_with_score(query, k=k)
        except Exception:
            docs = self.vectorstore.similarity_search(query, k=k)
            return [(doc, None) for doc in docs]

    def _normalize_and_trim(
        self,
        docs_and_scores: Sequence[Tuple[Document, Optional[float]]],
        final_k: int,
    ) -> List[RetrievedChunk]:
        """
        Deduplicate and normalize raw retrieval results.
        Keeps the first/best occurrence of repeated content.
        """
        normalized: List[RetrievedChunk] = []
        seen_keys: set[str] = set()

        for doc, score in docs_and_scores:
            content = (doc.page_content or "").strip()
            if not content:
                continue

            source = self._extract_source(doc)
            dedupe_key = self._make_dedupe_key(content, source)

            if dedupe_key in seen_keys:
                continue

            seen_keys.add(dedupe_key)
            normalized.append(
                RetrievedChunk(
                    content=content,
                    source=source,
                    score=score,
                    metadata=doc.metadata or {},
                )
            )

        # Sort by score when available.
        # With many vector backends, smaller distance can mean better match.
        # We place scored results first and sort ascending for consistency.
        normalized.sort(
            key=lambda chunk: (
                chunk.score is None,
                chunk.score if chunk.score is not None else float("inf"),
            )
        )

        return normalized[:final_k]

    # -----------------------------------------------------------------------
    # Query generation helpers
    # -----------------------------------------------------------------------

    def _generate_fusion_queries(self, query: str) -> List[str]:
        """
        Generate multiple semantically-related search queries.

        If no LLM is provided, falls back to lightweight manual expansions.
        """
        if self.llm is None:
            return self._fallback_fusion_queries(query)

        prompt = f"""
You are helping generate search queries for technical documentation retrieval.

Given the user's question, produce 4 alternative search queries that:
- preserve the original meaning
- use documentation-style phrasing
- include important library names if present
- help retrieve complementary chunks

Return only the queries, one per line, with no numbering.

User question:
{query}
""".strip()

        try:
            response = self.llm.invoke(prompt)
            text = self._extract_llm_text(response)
            queries = [line.strip("-• \t") for line in text.splitlines() if line.strip()]
            queries = [q for q in queries if q]
            if query not in queries:
                queries.insert(0, query)
            return queries[:5] if queries else self._fallback_fusion_queries(query)
        except Exception:
            return self._fallback_fusion_queries(query)

    def _fallback_fusion_queries(self, query: str) -> List[str]:
        """Simple fallback query expansion when no LLM is available."""
        variants = [
            query,
            f"{query} example",
            f"{query} documentation",
            f"{query} tutorial",
            f"{query} reference",
        ]

        seen = set()
        deduped: List[str] = []
        for item in variants:
            key = item.lower().strip()
            if key not in seen:
                seen.add(key)
                deduped.append(item)

        return deduped[:5]

    def _generate_hypothetical_document(self, query: str) -> str:
        """
        Generate a hypothetical ideal answer/document for HyDE retrieval.
        """
        if self.llm is None:
            return (
                f"Technical documentation explaining the following concept in detail:\n\n"
                f"{query}\n\n"
                f"Include API usage, examples, and best practices."
            )

        prompt = f"""
Write a concise technical documentation passage that would likely answer this question.

The passage should:
- sound like real documentation
- mention relevant APIs, methods, or concepts
- include a short example if appropriate
- stay focused on retrieval usefulness, not conversational style

Question:
{query}
""".strip()

        try:
            response = self.llm.invoke(prompt)
            text = self._extract_llm_text(response)
            return text.strip() if text.strip() else query
        except Exception:
            return query

    # -----------------------------------------------------------------------
    # Formatting / utility helpers
    # -----------------------------------------------------------------------

    def _extract_source(self, doc: Document) -> str:
        """
        Best-effort source extraction from document metadata.
        """
        metadata = doc.metadata or {}
        for key in ("source", "file_path", "path", "url", "title"):
            value = metadata.get(key)
            if value:
                return str(value)
        return "unknown"

    def _make_dedupe_key(self, content: str, source: str) -> str:
        """
        Build a lightweight dedupe key.
        """
        snippet = content[:200].strip().lower()
        return f"{source.lower()}::{snippet}"

    def _extract_llm_text(self, response: Any) -> str:
        """
        Normalize LLM response shapes across providers.
        """
        if response is None:
            return ""

        if isinstance(response, str):
            return response

        content = getattr(response, "content", None)
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            parts: List[str] = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict) and "text" in item:
                    parts.append(str(item["text"]))
                elif hasattr(item, "text"):
                    parts.append(str(item.text))
            return "\n".join(parts)

        return str(response)


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------

def create_retriever(
    persist_directory: str,
    embedding_model: Any,
    llm: Optional[Any] = None,
    collection_name: str = "docs",
    strategy: str = "fusion",
    k: int = 5,
    fetch_k: int = 10,
) -> DocumentationRetriever:
    """
    Factory helper so the rest of the app can create a retriever cleanly.
    """
    return DocumentationRetriever(
        persist_directory=persist_directory,
        embedding_model=embedding_model,
        llm=llm,
        collection_name=collection_name,
        strategy=strategy,
        k=k,
        fetch_k=fetch_k,
    )


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("retrieval.py loaded successfully.")
    print("Instantiate DocumentationRetriever from your MCP server.")