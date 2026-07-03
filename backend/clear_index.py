from dotenv import load_dotenv
load_dotenv()

import os
from pinecone import Pinecone

NAMESPACE = os.getenv("PINECONE_NAMESPACE", "default")

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))

if __name__ == "__main__":
    print(f"Clearing Pinecone namespace: {NAMESPACE}")
    index.delete(delete_all=True, namespace=NAMESPACE)
    print("Done clearing namespace.")
