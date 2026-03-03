# RAG SYSTEM

This is mini RAG System for Question and answering from PDF and TXT 

## Requirements :

- Python 3.11 or later
  
## Setup and Installation

Follow these steps to get the environment ready using `uv`:

### 1. Install uv
If you don't have `uv` installed yet, run the following command:
```bash
pip install uv
```
### 2. Create a Virtual Environment
```bash
uv venv --python 3.11
```
### 3. Activate the Environment
```bash
source .venv/bin/activate
```
### 4. Install Dependencies
Once your virtual environment is activated, use `uv` to sync all packages defined in `pyproject.toml`:

```bash
uv sync
```
### 5. Environment Setup
Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
Open `.env` and Set yours `Keys` and `variables`

## API Testing

You can test the FastAPI endpoints using the provided Postman collection.
### How to Run Application:
   ```bash
uv run uvicorn main:app --reload
```
we add `--reload` for if you Restarts the server automatically whenever you save changes to your code
### Download Postman Collection
* **File Path:** [RAG-System_Collection.json](./assets/postman/collections/New%20Collection.postman_collection.json)

### How to use:
1. Open **Postman**.
2. Click the **Import** button.
3. Drag and drop the file from the `assets/postman/collections/` directory.
4. Set your environment variable `api` to `http://127.0.0.1:8000`.