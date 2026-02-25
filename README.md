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
## How to Run Application:

