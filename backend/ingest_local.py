from dotenv import load_dotenv
load_dotenv()

import os
from rag_utils import upsert_documents, chunk_text

DATA_DIR = "data"


def load_files_as_docs():
    docs = []
    for filename in sorted(os.listdir(DATA_DIR)):
        if not filename.lower().endswith((".txt", ".md")):
            continue

        path = os.path.join(DATA_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = chunk_text(text, max_chars=800)
        for idx, chunk in enumerate(chunks):
            docs.append({
                "id": f"{filename}-{idx}",
                "text": chunk,
                "source": filename,
            })
    return docs


if __name__ == "__main__":
    docs = load_files_as_docs()
    print(f"Loaded {len(docs)} chunks to upsert...")
    upsert_documents(docs)
    print("Done upserting to Pinecone.")

