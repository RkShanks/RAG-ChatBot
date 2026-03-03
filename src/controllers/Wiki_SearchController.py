import io

import wikipediaapi
from fastapi import UploadFile

from .BaseController import BaseController


class Wiki_SearchController(BaseController):
    def __init__(self):
        super().__init__()

    def search_wikipedia(self, query: str, language: str = "en"):
        wiki = wikipediaapi.Wikipedia(
            user_agent="RAG-ChatBot/1.0 (zid.omar128885@gmail.com)", language="en"
        )
        # search for the query and return the results
        page = wiki.page(query)
        if page.exists():
            return page
        else:
            return None

    def get_UploadFile(self, page):
        # Read the content of the wiki file and return it as a UploadFile

        # step 1 : create a temporary file in memory
        content = f"Title: {page.title}\n\n{page.text}"
        file_bytes = content.encode("utf-8")

        # step 2 : create a UploadFile object
        upload_file = UploadFile(
            filename=f"{page.title}.txt",
            file=io.BytesIO(file_bytes),
        )
        return upload_file
