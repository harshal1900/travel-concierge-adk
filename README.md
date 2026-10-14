# Smart Travel & Local Experience Concierge

FastAPI + Google ADK + Gemini backend (Python 3.14). See `docs/PRD.md` and `docs/delivery-plan.md`.

## Run locally
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env        # add GOOGLE_API_KEY
uvicorn main:app --port 8000
```

## Try it
```bash
curl -s -X POST localhost:8000/api/chat -H 'content-type: application/json' \
  -d '{"message":"Plan a day in Tokyo with sightseeing and dinner"}'
```
Returns `{status, agent_text, a2ui_payload}`; a combined request returns both `attractions_card_list` and `dining_card_list`.

## Notes
- `DATA_PROVIDER=mock` (default) reads demo records from `data/*.json` (Tokyo, Paris, generic fallback). Ratings and prices are demo data, not live facts. A new city only needs a JSON entry.
- Sessions use `InMemorySessionService`: process-local, reset on restart.
- Tests: `python -m pytest` (deterministic, no network or API key needed).
