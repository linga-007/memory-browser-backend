# Memory Browser Backend

FastAPI backend for saving page content, generating embeddings, and searching stored memory with ChromaDB.

## Requirements

- Python 3.10 or newer
- Internet access the first time the embedding model is downloaded

## Setup

1. Create a virtual environment:

   ```powershell
   python -m venv venv
   ```

2. Activate it:

   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

3. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

## Run

Start the API with Uvicorn:

```powershell
uvicorn app:app --reload
```

The server runs at `http://127.0.0.1:8000` by default.

## API Endpoints

- `POST /save` - stores a page using `url`, `title`, and `content`
- `POST /search` - searches stored content using a query string
- `GET /history` - returns all stored records

## Notes

- The embedding model used is `all-MiniLM-L6-v2` from `sentence-transformers`.
- This project should not commit the local `venv/` folder or Python cache files.

## Deploy on Vercel

1. Commit and push this repository to Git (GitHub, GitLab, etc.).
2. In Vercel, create a new project and import the repository.
3. Vercel will use the `vercel.json` builder (`@vercel/python`) to deploy the ASGI `app` exported from `api/index.py`.
4. Ensure any required environment variables (for embeddings or DB connections) are added in the Vercel project settings.
5. After deployment, your API will be available at the Vercel-assigned URL.

Notes:
- Serverless functions have execution time and size limits; large model downloads may fail. Consider using external embedding services or precomputed embeddings for production.
