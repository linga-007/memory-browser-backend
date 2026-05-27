from functools import lru_cache

from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=1)
def get_model():

    return SentenceTransformer(
        "all-MiniLM-L6-v2"
    )

def generate_embedding(text):

    return get_model().encode(text).tolist()