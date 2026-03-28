"""
chat.py

CLI chat interface for the coding assistant.
Handles the user interaction loop and routes messages to the agent / LLM.
"""

from rich.console import Console
from rich.prompt import Prompt

from artifacts import (
    show_banner,
    render_user_task,
    render_assistant_message,
    render_error,
)

from retrieval import create_retriever


class ChatSession:
    """
    Main CLI chat session.
    """

    def __init__(self, llm=None, retriever=None):
        self.console = Console()
        self.llm = llm
        self.retriever = retriever

    def process_query(self, query: str) -> str:
        """
        Process a user query.

        If retrieval is available, augment context.
        """
        context = ""

        if self.retriever:
            try:
                docs = self.retriever.retrieve_as_text(query)
                context = f"\nRelevant Documentation:\n{docs}\n"
            except Exception as e:
                render_error(self.console, "Retrieval failed", str(e))

        prompt = f"""
You are an AI coding assistant.

User Question:
{query}

{context}

Provide a helpful answer.
"""

        if self.llm is None:
            return "No LLM configured."

        try:
            response = self.llm.invoke(prompt)
            return getattr(response, "content", str(response))
        except Exception as e:
            return f"LLM error: {e}"

    def start(self):
        """
        Start the CLI chat loop.
        """

        show_banner(self.console, "ForgeCode", "Autonomous CLI coding assistant")

        self.console.print("\nType 'exit' to quit.\n")

        while True:
            try:
                user_input = Prompt.ask("[bold yellow]You[/bold yellow]")

                if user_input.lower() in ["exit", "quit"]:
                    self.console.print("\nGoodbye.\n")
                    break

                render_user_task(self.console, user_input)

                response = self.process_query(user_input)

                render_assistant_message(self.console, response)

            except KeyboardInterrupt:
                self.console.print("\nSession ended.\n")
                break

            except Exception as e:
                render_error(self.console, "Unexpected error", str(e))


def run_chat(llm=None):
    """
    Entry point for starting a chat session.
    """

    retriever = None

    try:
        from langchain_ollama import OllamaEmbeddings

        embeddings = OllamaEmbeddings(model="nomic-embed-text")

        retriever = create_retriever(
            persist_directory="./chroma_db",
            embedding_model=embeddings,
            llm=llm,
            strategy="fusion",
        )

    except Exception:
        pass

    session = ChatSession(llm=llm, retriever=retriever)
    session.start()


if __name__ == "__main__":
    run_chat()
