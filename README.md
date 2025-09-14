echo "# Fullstack Assignment

## Structure
- frontend: Next.js (TS, Tailwind)
- backend: FastAPI + SQLAlchemy/SQLModel + Alembic
- docker: Docker Compose (Postgres DB)

## Getting Started
1. cd docker && docker compose up -d   # Start DB
2. cd backend && uvicorn main:app --reload
3. cd frontend && npm run dev
" > README.md
