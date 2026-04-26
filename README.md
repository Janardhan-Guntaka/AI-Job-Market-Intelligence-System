# CareerOps AI — Job Intelligence Platform

<div align="center">

![CareerOps AI](https://img.shields.io/badge/CareerOps-AI-6366f1?style=for-the-badge&logo=openai&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![LangChain](https://img.shields.io/badge/LangChain-RAG-121212?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**An open-source AI-powered career intelligence tool that matches your resume to live job listings using LangChain RAG + semantic embeddings.**

[Features](#-features) • [Architecture](#-architecture) • [Quick Start](#-quick-start) • [Contributing](#-contributing)

</div>

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **AI Job Matching** | LangChain + FAISS semantic search ranks jobs by resume similarity |
| 📄 **Resume Upload** | Drag-drop PDF/DOCX → AI extracts skills, experience level, job titles |
| 💡 **GPT Explanations** | GPT-3.5-turbo writes personalized "why this job fits you" for each result |
| 🌐 **5 Live Portals** | Remotive, RemoteOK, Jobicy, We Work Remotely, Adzuna |
| 📊 **Market Intelligence** | Real-time hiring trends, salary benchmarks, skill demand radar |
| 🔐 **Auth** | Google OAuth 2.0 + JWT session management |
| ⚡ **On-Demand Scraping** | Trigger live scrapes from the UI or via GitHub Actions schedule |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     React Frontend (Vite)                        │
│   Dashboard | JobExplorer | Analytics | CareerOps AI            │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API
┌────────────────────────────▼────────────────────────────────────┐
│                    FastAPI Backend (Python)                       │
│                                                                   │
│  /api/resume  ─── Upload → Parse → Match (LangChain RAG)        │
│  /api/jobs    ─── CRUD + filters + on-demand scrape trigger      │
│  /api/stats   ─── Trends, salary benchmarks, skill stats        │
│  /api/auth    ─── Google OAuth → JWT                             │
│                                                                   │
│  ┌──────────────────┐   ┌────────────────────────────────────┐  │
│  │ LangChain RAG    │   │ Multi-Portal Scraper               │  │
│  │ ─ FAISS index    │   │ ─ Remotive (API)                   │  │
│  │ ─ OpenAI embed   │   │ ─ RemoteOK (API)                   │  │
│  │ ─ GPT-3.5 chat   │   │ ─ Jobicy   (API)                   │  │
│  │ ─ HF fallback    │   │ ─ WeWorkRemotely (RSS)             │  │
│  └──────────────────┘   │ ─ Adzuna  (API, optional)          │  │
│                          └────────────────────────────────────┘  │
│                                                                   │
│  SQLite (dev) / PostgreSQL (prod)                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Google OAuth client credentials (for login)
- OpenAI API key *(optional — free HuggingFace fallback included)*

### 1. Clone & configure

```bash
git clone https://github.com/YOUR_USERNAME/AI_Job_Intelligence_Platform.git
cd AI_Job_Intelligence_Platform

# Server
cp server/.env.example server/.env
# Edit server/.env — add your GOOGLE_CLIENT_ID, JWT_SECRET, and optionally OPENAI_API_KEY

# Client
cp client/.env.example client/.env
# Edit client/.env — add your VITE_GOOGLE_CLIENT_ID
```

### 2. Run the backend

```bash
cd server
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Seed initial job data

```bash
# Option A: run the scraper directly
cd server && python scripts/run_scraper.py

# Option B: trigger via API (once server is running)
curl -X POST http://localhost:8000/api/scrape
```

### 4. Run the frontend

```bash
cd client
npm install
npm run dev
```

Open **http://localhost:5173** → Login with Google → Upload resume → Find jobs!

### Docker (all-in-one)

```bash
# Copy env files first (see step 1 above)
docker-compose up --build
```

---

## 🧠 AI Matching — How It Works

1. **Upload** your resume (PDF/DOCX/TXT)
2. Server extracts raw text and detects skills using a curated taxonomy of 100+ technologies
3. All jobs in the database are embedded into an **in-memory FAISS vector store** using OpenAI or HuggingFace sentence embeddings
4. Your resume text is used as the **semantic query** — top-K most similar jobs are retrieved
5. For each result, **GPT-3.5-turbo generates a personalized 1-sentence explanation** of why the job fits you
6. Results are ranked by similarity score with a match percentage ring

> **No OpenAI key?** The system automatically falls back to `sentence-transformers/all-MiniLM-L6-v2` (free, runs locally) for embeddings and uses template-based explanations. No functionality is lost, just slightly less polished explanations.

---

## 🌐 Job Portal Coverage

| Portal | Method | Rate | Free? |
|---|---|---|---|
| [Remotive](https://remotive.com/api) | JSON API | 200 jobs/call | ✅ |
| [RemoteOK](https://remoteok.com/api) | JSON API | ~100 jobs | ✅ |
| [Jobicy](https://jobicy.com/api/v2/remote-jobs) | JSON API | 50 jobs/call | ✅ |
| [We Work Remotely](https://weworkremotely.com) | RSS Feed | Live | ✅ |
| [Adzuna](https://developer.adzuna.com) | JSON API | 50/call, multi-country | ✅ (free key) |

---

## 📡 API Reference

Full interactive docs at **http://localhost:8000/docs**

| Endpoint | Method | Description |
|---|---|---|
| `/api/jobs` | GET | List jobs with filters (search, category, remote, salary, source) |
| `/api/scrape` | POST | Trigger on-demand scrape across all portals |
| `/api/resume/upload` | POST | Upload resume (PDF/DOCX/TXT) |
| `/api/resume/me` | GET | Get your parsed resume summary |
| `/api/resume/match` | POST | Run AI job matching |
| `/api/stats/summary` | GET | Dashboard KPIs |
| `/api/stats/skills` | GET | Top in-demand skills |
| `/api/stats/salary` | GET | Salary by category |
| `/api/stats/trends` | GET | Weekly hiring trends |
| `/api/auth/google` | POST | Google OAuth login |

---

## 🤝 Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines on:
- Adding new job portal scrapers
- Improving the RAG pipeline
- Frontend component contributions

---

## 📄 License

MIT — free to use, modify, and distribute. Attribution appreciated.

---

<div align="center">
Built with ❤️ as an open-source tool for students and job seekers.
</div>
