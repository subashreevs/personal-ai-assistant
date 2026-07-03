#RAG ENGINE
# | Function           | What it does                             | Why it's needed                  |
# | ------------------ | ---------------------------------------- | -------------------------------- |
# | `get_embedding`    | Turns text â†’ vector                      | Pinecone stores/searches vectors |
# | `chunk_text`       | Splits large docs into smaller chunks    | Better accuracy, cheaper         |
# | `upsert_documents` | Stores embeddings + metadata in Pinecone | Builds your knowledge base       |
# | `query_similar`    | Finds most relevant chunks to a question | Sends useful context to LLM      |


from dotenv import load_dotenv
load_dotenv()

import os
from typing import List, Dict
from openai import OpenAI
from pinecone import Pinecone

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = os.getenv("PINECONE_INDEX_NAME")
index = pc.Index(index_name)


def get_embedding(text: str) -> List[float]:
    """
    Get an embedding vector for a given text.
    """
    text = text.replace("\n", " ")
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding


def chunk_text(text: str, max_chars: int = 500) -> List[str]:
    """
    Very simple character-based chunking.
    Later you can improve with sentence/token-based chunking.
    """
    chunks = []
    text = text.strip()
    for i in range(0, len(text), max_chars):
        chunk = text[i:i+max_chars]
        chunks.append(chunk)
    return chunks


def upsert_documents(
    docs: List[Dict[str, str]],
    namespace: str = "default"
):
    """
    docs = [
      {"id": "doc1", "text": "some text", "source": "resume"},
      ...
    ]
    """
    vectors = []
    for doc in docs:
        embedding = get_embedding(doc["text"])
        vectors.append({
            "id": doc["id"],
            "values": embedding,
            "metadata": {
                "source": doc.get("source", "unknown"),
                "raw_text": doc["text"]
            }
        })
    index.upsert(vectors=vectors, namespace=namespace)


def query_similar(
    query: str,
    top_k: int = 5,
    namespace: str = "default"
):
    """
    Search Pinecone using the embedding of the query.
    """
    query_embedding = get_embedding(query)
    result = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True,
        namespace=namespace
    )
    return result
