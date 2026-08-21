seeding prod db: uv run --directory backend python ../scripts/seed_data.py --confirm-prod


Start local Docker services:
`docker compose up -d`

Run database seed (targets localhost:5432):
`uv run --directory backend python ../scripts/seed_data.py`

Run local backend:
`uv run --directory backend uvicorn app.main:app --reload --port 8000`

Run local frontend:
`cd frontend && npm run dev`