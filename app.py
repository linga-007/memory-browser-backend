from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone

from embeddings import generate_embedding
from db import build_search_payload, collect_stored_ids, fetch_records, get_pinecone_index, get_pinecone_namespace, response_value

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.post("/save")
async def save_page(data: dict):

    index = get_pinecone_index()

    existing = index.fetch(
        ids=[data["url"]]
    )

    existing_vectors = response_value(existing, "vectors", {})

    if existing_vectors:
        return {"message": "exists"}

    embedding = generate_embedding(
        data["content"]
    )

    index.upsert(
        vectors=[{
            "id": data["url"],
            "values": embedding,
            "metadata": {
                "title": data["title"],
                "url": data["url"],
                "content": data["content"],
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        }],
        namespace=get_pinecone_namespace()
    )

    return {"message": "saved", "namespace": get_pinecone_namespace()}


@app.post("/search")
async def search(data: dict):

    index = get_pinecone_index()

    embedding = generate_embedding(
        data["query"]
    )

    results = index.query(
        vector=embedding,
        top_k=5,
        include_metadata=True,
        namespace=get_pinecone_namespace()
    )
    print(results)

    return build_search_payload(results)


@app.get("/history")
async def get_history():

    index = get_pinecone_index()

    stored_ids = collect_stored_ids(index)

    results = fetch_records(index, stored_ids)
    print(results)

    return results