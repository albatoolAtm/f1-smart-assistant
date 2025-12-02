# f1-project (ED-CMR-GF MVP backend)

This folder contains a minimal FastAPI backend for the ED-CMR-GF project.

Run instructions (in VS Code):
1. python -m venv .venv
2. source .venv/bin/activate   # or .venv\Scripts\activate on Windows
3. pip install -r requirements.txt
4. put your API key in .env (OPENAI_API_KEY)
5. uvicorn app.main:app --reload --port 8000

Endpoints:
- GET /api/health
- POST /api/query

Place small model/data files into `app/models/` (passages.json, telemetry_embeddings.json)
