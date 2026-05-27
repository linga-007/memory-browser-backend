import chromadb

client = chromadb.Client()

collection = client.get_or_create_collection(
    name="memory_browser"
)