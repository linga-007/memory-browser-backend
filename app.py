from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from embeddings import generate_embedding
from db import collection

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.post("/save")
async def save_page(data: dict):

    existing = collection.get(
        ids=[data["url"]]
    )

    if existing["ids"]:
        return {"message": "exists"}

    embedding = generate_embedding(
        data["content"]
    )

    collection.add(
        documents=[data["content"]],
        embeddings=[embedding],
        ids=[data["url"]],
        metadatas=[{
            "title": data["title"],
            "url": data["url"]
        }]
    )

    return {"message": "saved"}

@app.post("/search")
async def search(data: dict):

    embedding = generate_embedding(
        data["query"]
    )

    results = collection.query(
        query_embeddings=[embedding],
        n_results=5
    )
    print(results)

    return results

@app.get("/history")
async def get_history():

    results = collection.get()
    print(results)

    return results