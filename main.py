from fastapi import FastAPI

app = FastAPI()


@app.get("/Welcome")
def welcome():
    return {
        "message": "Welcome to the RAG ChatBot!",
        "error": "none",
    }
