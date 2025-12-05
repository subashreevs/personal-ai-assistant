from dotenv import load_dotenv
load_dotenv()

import os
import uuid
from rag_utils import upsert_documents

DATA_DIR = "data"


def load_files_as_docs():
    docs = []
    for filename in os.listdir(DATA_DIR):
        if not filename.lower().endswith((".txt", ".md")):
            continue
        path = os.path.join(DATA_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        source = filename
        # simple chunking by ~500 chars
        from rag_utils import chunk_text
        chunks = chunk_text(text, max_chars=500)
        for chunk in chunks:
            doc_id = str(uuid.uuid4())
            docs.append({
                "id": doc_id,
                "text": chunk,
                "source": source
            })
    return docs


if __name__ == "__main__":
    docs = load_files_as_docs()
    print(f"Loaded {len(docs)} chunks to upsert...")
    upsert_documents(docs)
    print("Done upserting to Pinecone.")