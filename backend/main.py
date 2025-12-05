import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone
from rag_utils import query_similar

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = os.getenv("PINECONE_INDEX_NAME")
pinecone_index = pc.Index(index_name)

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4.1-mini")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later restrict to your Vercel domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


class ChatRequest(BaseModel):
    question: str


@app.post("/chat")
def chat(req: ChatRequest):
    # 1) retrieve similar chunks
    results = query_similar(req.question, top_k=5)

    # 2) build context string
    context_parts = []
    for match in results.matches:
        meta = match.metadata or {}
        chunk_text = meta.get("raw_text", "")
        src = meta.get("source", "unknown")
        context_parts.append(f"[Source: {src}]\n{chunk_text}")
    context = "\n\n".join(context_parts)

    # 3) system + user message to LLM
    system_prompt = (
        "You are a personal AI assistant that only answers "
        "based on the provided CONTEXT about the user. "
        "If something is not in the context, say you don't know."
    )

    user_message = (
        f"Question: {req.question}\n\n"
        f"CONTEXT from user's documents:\n{context}"
    )

    completion = openai_client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0.2,
    )

    answer = completion.choices[0].message.content

    return {
        "answer": answer,
        "sources": [
            {
                "id": m.id,
                "score": m.score,
                "source": (m.metadata or {}).get("source", "unknown"),
            }
            for m in results.matches
        ],
    }