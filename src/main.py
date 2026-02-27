from fastapi import FastAPI

from routes import base, data, wiki_search

app = FastAPI()

app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(wiki_search.wiki_search_router)
