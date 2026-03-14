from abc import ABC, abstractmethod
from typing import Dict, List


class LLMInterface(ABC):
    """
    Abstract Base Class for all LLM providers (OpenAI, Gemini, Local, etc.).
    Enforces a strict contract so the rest of the RAG system can swap models seamlessly.
    """

    @abstractmethod
    def set_generation_model(self, model_id: str):
        """
        Set the specific model version for text generation
        (e.g., 'gpt-4o', 'gemini-1.5-pro', 'llama3').
        """
        pass

    @abstractmethod
    def set_embedding_model(self, model_id: str, embedding_size: int = None):
        """
        Set the specific model version for generating vector embeddings.

        :param model_id: The identifier for the model (e.g., 'text-embedding-3-small').
        :param embedding_size: The target dimension size for the vector database.
                               Used for truncation (OpenAI) or DB index verification.
        """
        pass

    @abstractmethod
    async def generate_text(
        self, prompt: str, chat_history: List[Dict[str, str]] = None, max_output_tokens: int = None, **kwargs
    ) -> str:
        """
        Generate a text response from the LLM based on a prompt and optional chat history.

        :param prompt: The user's question or instruction.
        :param chat_history: A list of previous messages for context [{"role": "user", "content": "..."}, ...].
        :param kwargs: Additional parameters like temperature, max_tokens, etc.
        :return: The generated text string.
        """
        pass

    @abstractmethod
    async def generate_embedding(self, text: str, input_type: str, **kwargs) -> List[float]:
        """
        Convert a chunk of text into a vector embedding array for MongoDB $vectorSearch.

        :param text: The raw text chunk (e.g., from your GenZ School documents).
        :param kwargs: Additional provider-specific parameters.
        :return: A list of floats representing the embedding vector.
        """
        pass

    @abstractmethod
    async def construct_prompt(self, prompt: str, role: str) -> dict:
        """
        Construct a prompt for a specific role (e.g., SYSTEM, USER, etc).

        :param prompt: The user's question or instruction.
        :param text: The role of prompt (e.g., SYSTEM, USER, etc).
        :param kwargs: Additional provider-specific parameters.
        :return: A list of floats representing the embedding vector.
        """
        pass
