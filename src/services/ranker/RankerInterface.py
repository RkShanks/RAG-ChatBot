from abc import ABC, abstractmethod
from typing import List

from models.db_schemes import RetrievedDocument


class RankerInterface(ABC):
    """
    Abstract Base Class for all Cross-Encoder Reranking models.
    """

    @abstractmethod
    async def rerank(self, query: str, documents: List[RetrievedDocument], top_k: int = 5) -> List[RetrievedDocument]:
        """
        Takes a user query and a list of retrieved documents, scores them,
        and returns the top_k most relevant documents.

        :param query: The user's search string.
        :param documents: A list of dictionaries, must contain a 'text' key.
        :param top_k: How many documents to return after scoring.
        :return: A list of documents sorted by relevance score.
        """
        pass
