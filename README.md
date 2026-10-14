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

## Live data (optional): Google Places
Set `DATA_PROVIDER=google_places` and `PLACES_API_KEY` (restrict the key to Places API (New)). The provider uses Text Search with a field mask including `rating` and `priceLevel`, which bills at the Enterprise SKU (check the current free allowance and pricing). Places content is not cached, per Google Maps Platform terms, and live results must be attributed to Google Maps in the client. On any error, timeout or empty result the API returns demo records and says so in `agent_text`.

## Other LLMs (untested)
`LLM_MODEL` accepts a Gemini name (tested) or a LiteLLM `provider/model` string. For the latter run `pip install -r requirements-litellm.txt` and set that provider's own API key variable. Only Gemini is tested.

## Web client
See `web/README.md`. Start the API on port 8000, then `cd web && npm run dev`.

## Security and operations
- `APP_ENV=production` requires `SERVICE_API_KEY`; clients send it as `X-API-Key`. The app also refuses to start if the Gemini key is missing, or if `DATA_PROVIDER=google_places` has no `PLACES_API_KEY`.
- `message` is 1 to 2000 characters; `user_id` and `session_id` are at most 64.
- `RATE_LIMIT` (for example `30/minute`) is enforced in-process per API key (or per client address without a key). It is process-local, matching the single-instance, in-memory-session design.
- `REQUEST_TIMEOUT_SECONDS` bounds one agent run (504 on timeout). Errors return a short message plus a `correlation_id` (also the `X-Correlation-ID` header); stack traces stay in server logs.
- CORS only allows the origins in `ALLOWED_ORIGINS`.
- Each request writes one JSON log line (correlation ID, user_id, session_id, routing, latency, status).
- If one specialist fails, the other's cards are still returned and `agent_text` says what is unavailable. Demo records are always labelled.
