import os
from functools import lru_cache
from pathlib import Path
from time import sleep

from dotenv import dotenv_values, load_dotenv
from pinecone import Pinecone, ServerlessSpec
from pinecone.exceptions import NotFoundException


_dotenv_path = Path(__file__).resolve().parent / ".env"
_dotenv_values = dotenv_values(_dotenv_path)

load_dotenv(dotenv_path=_dotenv_path, override=True)


def get_env(name, default=None):

    value = os.getenv(name)

    if value:
        return value

    fallback = _dotenv_values.get(name, default)

    if isinstance(fallback, str):
        return fallback.strip()

    return fallback


@lru_cache(maxsize=1)
def get_pinecone_index():

    api_key = get_env("PINECONE_API_KEY")
    index_name = get_env("PINECONE_INDEX_NAME", "memory-browser")
    pinecone_cloud = get_env("PINECONE_CLOUD", "aws")
    pinecone_region = get_env("PINECONE_REGION", "us-east-1")

    if not api_key:
        raise RuntimeError("PINECONE_API_KEY is not set")

    client = Pinecone(api_key=api_key)

    try:
        return client.Index(index_name)
    except NotFoundException:
        client.create_index(
            name=index_name,
            dimension=384,
            metric="cosine",
            spec=ServerlessSpec(
                cloud=pinecone_cloud,
                region=pinecone_region,
            ),
            timeout=60,
        )

        sleep(1)

        return client.Index(index_name)


def get_pinecone_namespace():

    return get_env("PINECONE_NAMESPACE", "memory-browser")


def response_value(response, key, default=None):

    if isinstance(response, dict):
        return response.get(key, default)

    return getattr(response, key, default)


def _extend_ids_from_mapping(ids, data):

    raw_ids = data.get("ids", [])

    if raw_ids and isinstance(raw_ids[0], list):
        for row in raw_ids:
            ids.extend(row)
        return

    ids.extend(raw_ids)


def _extend_ids_from_item(ids, item):

    if isinstance(item, str):
        ids.append(item)
        return

    if isinstance(item, dict):
        if "ids" in item and isinstance(item["ids"], list):
            ids.extend(item["ids"])
        elif "id" in item:
            ids.append(item["id"])
        return

    if isinstance(item, (list, tuple, set)):
        ids.extend(item)


def iter_ids(list_response):

    if list_response is None:
        return []

    ids = []

    if isinstance(list_response, dict):
        _extend_ids_from_mapping(ids, list_response)
        return ids

    for item in list_response:
        _extend_ids_from_item(ids, item)

    return ids


def vector_items_from_fetch(fetch_response):

    vectors = response_value(fetch_response, "vectors", {})

    if isinstance(vectors, dict):
        return list(vectors.items())

    if isinstance(vectors, list):
        return [(vector.get("id"), vector) for vector in vectors if isinstance(vector, dict)]

    return []


def _match_value(match, key, default=None):

    if isinstance(match, dict):
        return match.get(key, default)

    return getattr(match, key, default)


def _search_result_from_match(match):

    metadata = _match_value(match, "metadata", {})
    match_id = _match_value(match, "id")
    score = _match_value(match, "score")

    if not isinstance(metadata, dict):
        metadata = {}

    snippet = metadata.get("content", "")

    return {
        "id": match_id,
        "title": metadata.get("title", match_id),
        "url": metadata.get("url", match_id),
        "snippet": snippet,
        "summary": snippet,
        "score": score,
        "metadata": {**metadata, **({"score": score} if score is not None else {})},
    }


def build_history_payload(fetch_response):

    ids = []
    documents = []
    metadatas = []

    for vector_id, vector in vector_items_from_fetch(fetch_response):
        metadata = vector.get("metadata", {}) if isinstance(vector, dict) else {}

        ids.append(vector_id)
        documents.append(metadata.get("content", ""))
        metadatas.append({key: value for key, value in metadata.items() if key != "content"})

    return {
        "ids": [ids],
        "documents": [documents],
        "metadatas": [metadatas],
    }


def build_search_payload(query_response):

    matches = response_value(query_response, "matches", [])

    results = []
    ids = []
    documents = []
    metadatas = []

    for match in matches or []:
        result = _search_result_from_match(match)

        ids.append(result["id"])
        documents.append(result["snippet"])
        metadatas.append(result["metadata"])
        results.append(result)

    return {
        "results": results,
        "ids": [ids],
        "documents": [documents],
        "metadatas": [metadatas],
    }


def collect_stored_ids(index):

    try:
        return iter_ids(index.list(namespace=get_pinecone_namespace()))
    except Exception:
        return []


def fetch_records(index, ids):

    if not ids:
        return {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
        }

    records = {
        "ids": [],
        "documents": [],
        "metadatas": [],
    }

    for start in range(0, len(ids), 100):
        batch = ids[start:start + 100]
        fetched = index.fetch(ids=batch, namespace=get_pinecone_namespace())

        payload = build_history_payload(fetched)
        records["ids"].extend(payload["ids"][0])
        records["documents"].extend(payload["documents"][0])
        records["metadatas"].extend(payload["metadatas"][0])

    return {
        "ids": [records["ids"]],
        "documents": [records["documents"]],
        "metadatas": [records["metadatas"]],
    }