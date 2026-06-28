# 🧠 Agentic AI System for Multi-Step Tasks

> A production-ready, highly concurrent AI orchestration engine built completely from scratch without relying on black-box frameworks (like LangChain or CrewAI). 

This system accepts a complex user request, decomposes it into discrete steps (a Directed Acyclic Graph), assigns each step to a specialized agent, and dynamically streams the real-time execution state to a modern web UI.

---

## ✨ Key Features
*   **Custom DAG Orchestration:** Dynamically parses LLM output into a dependency graph of tasks.
*   **Manual Concurrent Batching:** Uses Python's `asyncio.gather` to execute tasks with fulfilled dependencies in parallel, drastically reducing total execution time.
*   **Real Tool Integration:** Agents don't just hallucinate facts. The `Retriever` agent uses native Python HTTP libraries to hit the live Wikipedia API, providing real-time data to downstream agents.
*   **Bulletproof JSON Mode:** Natively enforces Groq's JSON-mode at the API level to guarantee 100% valid task structures, eliminating parsing crashes.
*   **Robust Frontend Streaming:** Implements a custom Server-Sent Events (SSE) byte-buffer in Next.js to flawlessly reconstruct massive LLM payloads chopped by network latency.

## 🛠️ Technology Stack
*   **Frontend:** Next.js 14, React, TailwindCSS, Lucide Icons.
*   **Backend:** Python 3.10+, FastAPI, Uvicorn, `asyncio`, `sse-starlette`.
*   **AI Engine:** Groq API (`llama-3.3-70b-versatile`) for ultra-low latency inference.

---

## 🚀 Local Setup Instructions

### 1. Backend Setup
Navigate to the `backend` directory and set up the Python virtual environment:
```bash
cd backend
python -m venv venv
# Windows: .\venv\Scripts\Activate.ps1
# Mac/Linux: source venv/bin/activate

pip install -r requirements.txt # (or pip install fastapi uvicorn groq pydantic python-dotenv sse-starlette httpx)
```

Create a `.env` file in the `backend` directory and add your Groq API key:
```env
GROQ_API_KEY=your_api_key_here
```

Start the backend server:
```bash
uvicorn main:app --reload --port 8000
```

### 2. Frontend Setup
Open a new terminal, navigate to the `frontend` directory, and install dependencies:
```bash
cd frontend
npm install
```

Start the development server:
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser to access the UI.

---

## 📚 Deliverables
As requested by the assessment, the following documents are included in this repository:
*   [SYSTEM_DESIGN.md](./SYSTEM_DESIGN.md) - Covers the core architecture, data flow, and key architectural decisions.
*   [POST_MORTEM.md](./POST_MORTEM.md) - Details scaling constraints, design reflections, and explicit trade-offs made during development.

---

*Built with passion, technical rigor, and an obsession for clean architecture.*
