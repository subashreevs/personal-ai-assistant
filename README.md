# 🤖 Personal AI Assistant — Serverless RAG Chatbot  
_A production-ready, low-cost personal AI chatbot built with FastAPI, AWS Lambda, Pinecone, OpenAI, React, and Vercel._

This project builds a **personal AI assistant** capable of answering questions about **you** using Retrieval-Augmented Generation (RAG).  
It processes your documents (résumé, LinkedIn text, portfolio, etc.), embeds them into a vector database, retrieves relevant chunks, and generates accurate responses with GPT-4.1-mini.

This system is:

- ⚡ **Fast** — AWS Lambda + Vercel  
- 💰 **Cheap** — $2–$6/month  
- 🛠 **Zero-maintenance** — fully serverless  
- 🧠 **Smart** — OpenAI + Pinecone  
- 🔄 **Easy to update** — re-run ingestion script  

---

## 📘 Table of Contents
- [Overview](#-overview)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Backend Setup](#-backend-setup)
- [Document Ingestion](#-document-ingestion)
- [Deploy Backend to AWS Lambda](#-deploy-backend-to-aws-lambda)
- [Frontend Setup](#-frontend-setup)
- [Deploy Frontend to Vercel](#-deploy-frontend-to-vercel)
- [API Endpoints](#-api-endpoints)
- [RAG Workflow](#-rag-workflow)
- [Security](#-security)
- [Cost Breakdown](#-cost-breakdown)
- [Debugging Guide](#-debugging-guide)
- [Future Enhancements](#-future-enhancements)
- [License](#-license)

---

# 🧩 Overview
This AI assistant answers questions about **you**, grounded in your résumé, LinkedIn data, and documents.  
You control the knowledge base via a Pinecone vector index populated by an ingestion script.

The system uses:

- Text chunking  
- Semantic search via embeddings  
- Retrieval-Augmented Generation (RAG)  

---

# 🏗 Architecture

```
                    ┌──────────────────────────┐
                    │        Frontend (UI)      │
                    │ React + Vite + TS (Vercel)│
                    └──────────────┬────────────┘
                                   │ Axios POST /chat
                                   ▼
                    ┌──────────────────────────┐
                    │     AWS Lambda Function  │
                    │ FastAPI app via Mangum   │
                    └──────────────┬────────────┘
                                   │ Query Pinecone
                                   ▼
                    ┌──────────────────────────┐
                    │     Pinecone Vector DB   │
                    └──────────────┬────────────┘
                                   │ Context retrieved
                                   ▼
                    ┌──────────────────────────┐
                    │   OpenAI GPT-4.1-mini    │
                    └──────────────┬────────────┘
                                   │ Answer
                                   ▼
                    ┌──────────────────────────┐
                    │ Returned to Frontend UI  │
                    └──────────────────────────┘
```

---

# 🛠 Tech Stack

### **Frontend**
- React (Vite, TypeScript)
- Axios
- Responsive chat UI
- Hosted on **Vercel**

### **Backend**
- FastAPI
- Mangum (ASGI → Lambda adapter)
- Python 3.11

### **Vector Database**
- Pinecone (Starter tier — free)

### **LLM**
- OpenAI GPT-4.1-mini
- Embeddings: text-embedding-3-small

### **Cloud**
- AWS Lambda (FastAPI via Mangum)
- Lambda Function URL (public API)

---

# 📁 Project Structure

```
personal-ai-assistant/
│
├── backend/
│   ├── main.py               # FastAPI backend + RAG logic
│   ├── rag_utils.py          # Retrieval helper functions
│   ├── ingest_local.py       # Script to ingest user docs → Pinecone
│   ├── requirements.txt
│   ├── backend.zip           # Lambda deployment ZIP
│   └── .env                  # Local-only env variables
│
└── frontend/
    ├── src/
    │   ├── App.tsx
    │   ├── App.css
    ├── index.html
    ├── vite.config.ts
```

---

# ⚙ Backend Setup

## 1️⃣ Install dependencies

```bash
pip install -r backend/requirements.txt
```

## 2️⃣ Create `.env` (local only)

```
OPENAI_API_KEY=your_key
PINECONE_API_KEY=your_key
PINECONE_INDEX_NAME=your_index
MODEL_NAME=gpt-4.1-mini
```

Lambda uses **real environment variables**, not `.env`.

---

# 📥 Document Ingestion

Run the ingestion script:

```bash
cd backend
python ingest_local.py
```

This:

- Loads your documents  
- Chunks them  
- Generates embeddings  
- Uploads to Pinecone  

Run again whenever your résumé changes.

---

# 🚀 Deploy Backend to AWS Lambda

You MUST build in a Linux environment using Docker.

## 1️⃣ Build deployment package

```bash
rmdir /s /q package
mkdir package
```

Install dependencies into package:

```bash
docker run --rm -v "%cd%":/app -w /app python:3.11     bash -c "pip install -r requirements.txt -t package/"
```

Copy backend files:

```bash
copy main.py packagecopy rag_utils.py package```

Zip the package:

```bash
powershell Compress-Archive -Path package\* -DestinationPath backend.zip -Force
```

---

## 2️⃣ Create Lambda Function

Settings:

- Runtime: **Python 3.11**
- Handler: `main.handler`
- Upload: `backend.zip`

---

## 3️⃣ Add Lambda Environment Variables

```
OPENAI_API_KEY=xxxx
PINECONE_API_KEY=xxxx
PINECONE_INDEX_NAME=xxxx
MODEL_NAME=gpt-4.1-mini
```

---

## 4️⃣ Configure Lambda Function URL

- Auth: NONE  
- **CORS: OFF**  
  (FastAPI handles all CORS)

Example API URL:

```
https://abc123xyz.lambda-url.us-east-1.on.aws
```

---

# 🌐 Frontend Setup

Install:

```bash
cd frontend
npm install
```

Run locally:

```bash
npm run dev
```

Update `.env` or Vite settings:

```
VITE_API_BASE_URL="https://your-lambda-url"
```

---

# 🚀 Deploy Frontend to Vercel

1. Push repo to GitHub  
2. Import into Vercel  
3. Add environment variable:

```
VITE_API_BASE_URL=https://your-lambda-url
```

4. Deploy  
5. Your chatbot is live 🎉  

---

# 🔌 API Endpoints

## **GET /health**

```json
{ "status": "ok" }
```

## **POST /chat**

### Request:

```json
{
  "question": "What skills does Suba have?"
}
```

### Response:

```json
{
  "answer": "Final answer...",
  "sources": [
    {
      "id": "chunk1",
      "score": 0.92,
      "source": "resume"
    }
  ]
}
```

---

# 🧠 RAG Workflow

1. User asks a question  
2. Retrieve relevant text chunks from Pinecone  
3. Build a context block  
4. Pass context + question → OpenAI  
5. GPT-4.1-mini produces grounded answer  
6. UI displays final output  

---

# 🔐 Security

- API keys stored **only inside Lambda environment**  
- Pinecone index is private  
- Vercel frontend exposes no secrets  
- HTTPS enforced everywhere  
- No user data stored on backend  

---

# 💸 Cost Breakdown

| Component       | Monthly Cost |
|----------------|--------------|
| AWS Lambda     | $0–$1 |
| Vercel         | Free |
| Pinecone       | Free |
| OpenAI         | $1–$5 |
| **Total**      | **$2–$6** |

---

# 🪵 Debugging Guide

### ❌ CORS issues  
Fix by:  
- Lambda CORS OFF  
- FastAPI CORS configured with your Vercel URL  
- `allow_headers=["*"]`

### ❌ 502 Bad Gateway  
- Wrong handler name  
- Missing Mangum handler  

### ❌ Import errors  
- Rebuild backend.zip using Docker  

### ❌ Pinecone errors  
- Wrong index name  
- No embeddings ingested  

---

# 🚀 Future Enhancements

- Streaming responses  
- Chat history (local or backend)  
- Admin dashboard  
- Multiple persona modes  
- S3 auto-ingestion  
- Support DeepSeek/Groq LLMs  
- UI themes + avatars  

---

# 📜 License

MIT License.

---

# 🎉 Final Note

This project is **portfolio-ready**, cloud-native, scalable, and extremely low-cost.  
It showcases real skills in:

- AI engineering  
- RAG systems  
- FastAPI  
- AWS serverless  
- React + frontend fundamentals  
- Vector DB search  

If you want a **PDF version**, **GitHub badges**, **diagrams**, or a **deployment video script**, just ask!
