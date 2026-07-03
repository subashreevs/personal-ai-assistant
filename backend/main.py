import os
from typing import Literal
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
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
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "3"))
MIN_SCORE = float(os.getenv("MIN_SCORE", "0.35"))
MAX_CONTEXT_CHARS = int(os.getenv("MAX_CONTEXT_CHARS", "2500"))
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

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


class ChatHistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    question: str
    history: list[ChatHistoryMessage] = Field(default_factory=list)


def read_data_file(filename: str, max_chars: int) -> str:
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read().strip()
    return text[:max_chars]


def supplemental_context_for(question: str) -> list[tuple[str, str]]:
    q = question.lower()
    files: list[tuple[str, int]] = []

    if any(term in q for term in ["contact", "email", "phone", "linkedin", "github", "portfolio", "reach"]):
        files.extend([("contact_links.txt", 900)])

    if any(term in q for term in ["current", "currently", "latest", "recent", "working", "work now"]):
        files.extend([("experience_stories.txt", 1800), ("about_me.txt", 700)])

    if any(term in q for term in ["good at", "strength", "strong", "hire", "fit", "role", "roles", "why her", "why should"]):
        files.extend([
            ("qa_examples.txt", 1600),
            ("about_me.txt", 900),
            ("skills_evidence.txt", 1800),
        ])

    if any(term in q for term in ["project", "built", "portfolio"]):
        files.extend([("projects.txt", 1800)])

    if any(term in q for term in ["certification", "certifications", "certificate", "aws", "nvidia", "safe"]):
        files.extend([("certifications.txt", 1600)])

    seen = set()
    snippets = []
    for filename, max_chars in files:
        if filename in seen:
            continue
        seen.add(filename)
        text = read_data_file(filename, max_chars)
        if text:
            snippets.append((filename, text))
    return snippets


def add_context_part(context_parts: list[str], source: str, text: str, total_chars: int) -> int:
    part = f"[Source: {source}]\n{text.strip()}"
    remaining = MAX_CONTEXT_CHARS - total_chars
    if remaining <= 0:
        return total_chars
    if len(part) > remaining:
        part = part[:remaining]
    context_parts.append(part)
    return total_chars + len(part)


def looks_like_profile_question(question: str, history: list[ChatHistoryMessage]) -> bool:
    q = f" {question.lower().strip()} "

    out_of_scope_terms = [
        "fibonacci", "leetcode", "homework", "solve this", "write code", "give me code",
        "python code", "javascript code", "java code", "c++ code", "algorithm for",
        "math concept", "calculus", "integral", "integration in math", "derivative",
        "divided by", "multiply", "equation", "what is 2", "what is 1", "what is 3",
    ]
    if any(term in q for term in out_of_scope_terms):
        return False

    profile_terms = [
        "subashree", "resume", "linkedin", "github", "portfolio", "email", "phone",
        "contact", "work", "experience", "job", "current", "currently", "latest",
        "project", "skill", "good at", "strength", "hire", "fit", "role", "certification",
        "certificate", "aws", "nvidia", "safe", "background", "education", "degree",
    ]
    pronoun_terms = [" she ", " her ", " hers "]
    if any(term in q for term in profile_terms) or any(term in q for term in pronoun_terms):
        return True

    followup_terms = [
        "why", "how", "explain", "example", "tell me more", "more", "what about",
        "summarize", "shorter", "expand", "details", "which one", "where", "when",
    ]
    if any(term in q for term in followup_terms):
        for item in reversed(history[-4:]):
            previous = item.content.lower()
            if previous.startswith("i am mainly here to answer questions about subashree"):
                continue
            if any(term in previous for term in profile_terms) or any(term in f" {previous} " for term in pronoun_terms):
                return True

    return False


def out_of_scope_answer() -> str:
    return (
        "I am mainly here to answer questions about Subashree's background, work, "
        "projects, skills, certifications, and contact links. Try asking me something about her."
    )


@app.post("/chat")
def chat(req: ChatRequest):
    if not looks_like_profile_question(req.question, req.history):
        return {"answer": out_of_scope_answer(), "sources": []}

    context_parts = []
    total_chars = 0

    for source, text in supplemental_context_for(req.question):
        total_chars = add_context_part(context_parts, source, text, total_chars)

    results = query_similar(req.question, top_k=RETRIEVAL_TOP_K)
    matches = [m for m in results.matches if m.score is None or m.score >= MIN_SCORE]

    for match in matches:
        meta = match.metadata or {}
        chunk_text = meta.get("raw_text", "").strip()
        src = meta.get("source", "unknown")
        if not chunk_text:
            continue
        total_chars = add_context_part(context_parts, src, chunk_text, total_chars)
        if total_chars >= MAX_CONTEXT_CHARS:
            break

    context = "\n\n".join(context_parts)

    system_prompt = (
        "You are Subashree's friendly personal assistant. "
        "Only answer questions about Subashree's background, work, projects, skills, certifications, education, and contact links. "
        "If the user asks for general coding help, math tutoring, homework, or anything unrelated to Subashree, briefly say you are here to answer questions about Subashree. "
        "Answer warmly, casually, and concisely while staying grounded in the provided CONTEXT. "
        "Use recent chat history only to understand short follow-up questions about Subashree. "
        "Subashree is targeting 2026 software engineering and AI-focused roles. "
        "For broad questions about what she is good at, lead with software engineering, AI/LLM applications, full-stack work, backend APIs, data pipelines, cloud, and data visualization. "
        "Mention mobile development only as an additional strength, or when the user specifically asks about mobile. "
        "For current or latest experience questions, use the most recent dated roles in the context and do not default to older Amadeus experience if newer roles are present. "
        "Use short paragraphs for simple answers and 3-5 bullets when the user asks for a summary, list, strengths, projects, or comparison. "
        "Avoid sounding like a formal recruiter summary unless the user specifically asks for that tone. "
        "Do not mention internal files, retrieval, vectors, or context. "
        "Do not use em dashes. Use commas, periods, or parentheses instead. "
        "If something about Subashree is not in the context, say you are not sure instead of guessing."
    )

    user_message = (
        f"Question: {req.question}\n\n"
        f"CONTEXT from user's documents:\n{context}"
    )

    messages = [{"role": "system", "content": system_prompt}]
    for item in req.history[-6:]:
        messages.append({"role": item.role, "content": item.content[:1000]})
    messages.append({"role": "user", "content": user_message})

    completion = openai_client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.2,
    )

    answer = completion.choices[0].message.content

    sources = [
        {
            "id": m.id,
            "score": m.score,
            "source": (m.metadata or {}).get("source", "unknown"),
        }
        for m in matches
    ]

    for source, _ in supplemental_context_for(req.question):
        if not any(item["source"] == source for item in sources):
            sources.insert(0, {"id": f"supplemental-{source}", "score": None, "source": source})

    return {"answer": answer, "sources": sources}


from mangum import Mangum
handler = Mangum(app)
