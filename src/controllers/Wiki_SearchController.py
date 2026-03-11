import io
import logging

import wikipediaapi
from fastapi import UploadFile

from helpers.config import get_settings
from models import ProcessingEnums

from .BaseController import BaseController

logger = logging.getLogger(__name__)
settings = get_settings()


class Wiki_SearchController(BaseController):
    def __init__(self):
        super().__init__()
        self.wiki_user_agent = settings.WIKI_USER_AGENT

    def search_wikipedia(self, query: str, language: str = "en"):
        logger.info(f"Initiating Wikipedia search for query: '{query}' (lang: {language})")
        try:
            wiki = wikipediaapi.Wikipedia(user_agent=self.wiki_user_agent, language=language)

            logger.debug(f"Fetching page data for '{query}' from Wikipedia API...")
            page = wiki.page(query)

            if page.exists():
                logger.info(f"Successfully found Wikipedia page: '{page.title}'")
                return page

            else:
                logger.warning(f"Wikipedia page not found for query: '{query}'")
                return None

        except Exception as e:
            # We catch it, log it, and re-raise it so the global handler can send a 500 error.
            logger.error(f"Failed to communicate with Wikipedia API for query '{query}': {e}")
            raise e

    def get_UploadFile(self, page):
        logger.debug(f"Converting Wikipedia page '{page.title}' into an in-memory UploadFile.")

        # step 1 : create a temporary file in memory
        content = f"Title: {page.title}\n\n{page.text}"
        file_bytes = content.encode("utf-8")

        # Calculate size for the log
        file_size_kb = len(file_bytes) / 1024

        # step 2 : create a UploadFile object
        filename = f"{page.title}{ProcessingEnums.MD.value}"
        upload_file = UploadFile(
            filename=filename,
            file=io.BytesIO(file_bytes),
        )

        logger.info(f"Successfully created UploadFile '{filename}' ({file_size_kb:.2f} KB)")

        return upload_file
