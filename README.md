# FireReach

FireReach is a full-stack outreach assistant that discovers live company signals, scores lead quality, and generates personalized outbound emails.

## Features

- FastAPI backend with authenticated endpoints for agent runs and history.
- LangGraph workflow for signal collection, analysis, scoring, strategy, and email generation.
- React + Vite frontend for running analyses and managing outreach records.
- SQLite persistence with SQLAlchemy and async access.
- Dockerized backend and frontend with a ready `docker-compose.yml`.

## Tech Stack

- Backend: Python, FastAPI, LangGraph, SQLAlchemy
- Frontend: React, Vite, Tailwind CSS
- Integrations: Serper, Groq/Ollama, SendGrid/SMTP, Hunter
- Runtime: Docker + Docker Compose

## Project Structure

```text
.
├── backend/
│   ├── agent/
│   ├── db/
│   ├── services/
│   ├── tests/
│   ├── Dockerfile
│   ├── .env.example
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml
└── README.md
```

## Local Development

### 1) Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload
```

Backend runs at `http://localhost:8000` and docs at `http://localhost:8000/docs`.

### 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

## Docker

```bash
docker compose up --build
```

Services:

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- Backend docs: `http://localhost:8000/docs`

## Configuration

Create `backend/.env` from `backend/.env.example` and set at least:

- `SERPER_API_KEY`
- `LLM_API_KEY` (for Groq) or configure Ollama fallback
- `SENDGRID_API_KEY` or SMTP credentials
- `JWT_SECRET_KEY`

## API Overview

Common endpoints:

- `POST /auth/signup`
- `POST /auth/login`
- `GET /auth/me`
- `POST /run-agent`
- `POST /batch-analyze`
- `GET /history`
- `GET /stats`
- `GET /health`

## Notes

- Prompt/reference markdown files are intentionally excluded from version control.
- Secrets are ignored via `.gitignore` (for example `backend/.env`).
