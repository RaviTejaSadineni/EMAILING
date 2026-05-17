# DMS Email Monitor

Contract Lifecycle Intelligence Platform foundation for legal contract email analytics. It provides FastAPI APIs, PostgreSQL/Redis infrastructure, JWT auth, WebSocket progress plumbing, and a React + Tailwind 3D-styled frontend shell.

## Tech Stack

- Backend: Python 3.13, FastAPI, SQLAlchemy 2.0 async, PostgreSQL 16, Redis, Alembic
- Frontend: React 18 + Vite + TailwindCSS
- Auth: Custom JWT (access + refresh tokens)
- AI config target: Azure OpenAI `gpt-5.4-mini-ravi`

## Configuration

Create `backend/.env` from `backend/.env.example`.

```env
APP_NAME=DMS Email Monitor
DEBUG=false
SECRET_KEY=replace-with-32-plus-character-secret-key
ALLOWED_ORIGINS=["http://localhost:5173","http://localhost:3000"]
DATABASE_URL=postgresql+asyncpg://postgres:app@localhost:5432/email_dig
REDIS_URL=redis://localhost:6379/0
AZURE_OPENAI_ENDPOINT=https://gaebtesting1.openai.azure.com
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_DEPLOYMENT=gpt-5.4-mini-ravi
SLR_WHITE_MINUTES=4
SLR_YELLOW_MINUTES=8
EMAIL_POLL_INTERVAL_SECONDS=30
MAX_EMAILS_PER_POLL=50
```

## Setup and Run

```bash
# Start services
docker-compose up -d

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Create database
# (PostgreSQL should be running via docker-compose)
# Create the database if it doesn't exist:
# docker exec -it postgres psql -U postgres -c "CREATE DATABASE email_dig;"

# Run migrations
alembic upgrade head

# Run backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest tests/ -v

# Frontend setup
cd ../frontend
npm install
npm run dev
```

## Alembic Commands Reference

```bash
# Generate new migration after model changes
alembic revision --autogenerate -m "description"

# Apply all migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

## Implemented Step 1 Endpoints

- Auth: `POST /auth/register`, `POST /auth/login`, `GET /auth/me`, `POST /auth/refresh`
- Health: `GET /health`, `GET /health/db`, `GET /health/redis`
- Imports: `POST /imports/upload`, `GET /imports/jobs`, `GET /imports/jobs/{id}`
- WebSocket: `WS /ws/progress/{job_id}`

## Step 2/3 Setup

```bash
cd backend
alembic upgrade head
pytest tests/ -v

cd ../frontend
npm install
npm install three @react-three/fiber @react-three/drei framer-motion react-circular-progressbar
npm run dev
```
