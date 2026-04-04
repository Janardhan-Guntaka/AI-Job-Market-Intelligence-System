# AI Job Market Intelligence System

A full-stack platform for real-time job market intelligence — salary trends, skill demand analysis, and hiring velocity metrics across 500+ live job postings.

## 🚀 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python · FastAPI · SQLAlchemy · SQLite |
| Frontend | React 18 · Vite · Tailwind CSS · Recharts |
| Testing | Pytest (async) · Playwright (e2e) |
| CI/CD | GitHub Actions |
| Deploy | Docker · docker-compose |

## 📁 Project Structure

```
AI_Job_Intelligence_Platform/
├── server/              # FastAPI backend
│   ├── app/
│   │   ├── main.py      # App entry point
│   │   ├── database.py  # SQLAlchemy + SQLite
│   │   ├── models/      # Job ORM model
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── api/         # REST route handlers
│   │   └── services/    # Data pipeline / seeder
│   ├── requirements.txt
│   └── Dockerfile
├── client/              # React + Vite + Tailwind
│   ├── src/
│   │   ├── pages/       # Dashboard, JobExplorer, Analytics
│   │   ├── components/  # Navbar, Sidebar, JobCard, KPICard, SkillBadge
│   │   └── api/         # Axios client
│   ├── package.json
│   └── vite.config.js
├── tests/
│   ├── backend/         # Pytest async API tests
│   └── frontend/        # Playwright UI tests
├── .github/workflows/   # CI/CD pipeline
└── docker-compose.yml
```

## ⚡ Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+

### Backend

```bash
cd server
pip install -r requirements.txt
uvicorn app.main:app --reload
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Frontend

```bash
cd client
npm install
npm run dev
# App: http://localhost:5173
```

### Docker (both services)

```bash
docker-compose up --build
```

## 🧪 Testing

### Backend (Pytest)
```bash
pytest tests/backend/ -v
```

### Frontend (Playwright)
```bash
cd tests/frontend
npm install @playwright/test
npx playwright install chromium
npx playwright test --config=playwright.config.js
```

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/jobs` | List jobs (paginated, filterable) |
| GET | `/api/jobs/{id}` | Get single job |
| GET | `/api/stats/summary` | KPI summary |
| GET | `/api/stats/skills` | Skill demand stats |
| GET | `/api/stats/salary` | Salary by category |
| GET | `/api/stats/trends` | Weekly hiring trends |
| GET | `/api/categories` | All categories |

## 📊 Features

- **Dashboard** — KPI cards, hiring trend chart, category breakdown, top skills
- **Job Explorer** — Search, filter by category/remote/experience/salary, paginated grid
- **Analytics** — Salary benchmarks, skill radar, dual-axis velocity chart, skills table
- **Data Pipeline** — 500 realistic jobs seeded on startup with Faker
