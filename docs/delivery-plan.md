# Travel Concierge — Production Delivery Plan (12–18 Oct 2026)

## Summary

The goal is a production-ready, public GitHub project by Sunday 18 Oct 2026: the PRD's `POST /api/chat` service, built to learn Google ADK and A2UI and to show as portfolio work. Saturday 17 and Sunday 18 Oct are buffer days. The PRD scope and API contract do not change.

Three rules shape the whole plan:

- **Bring your own keys (BYOK).** The LLM, its API key, the data source and the Google Places key are settings, never code. You use your own keys for development; anyone else adds theirs.
- **Deployment-ready, not deployed.** The repository holds no cloud-specific code. Going live later means following `production_live_steps.md`: buy and set up the cloud account, set the environment variables, deploy. No line of repository code changes.
- **Free first.** Development and sanity tests use the free Gemini API tier and the built-in JSON data provider. Paid services (Google Places, a cloud host) are used only when you decide.

"Production-ready" here means a real live-data provider that is built and tested (so the project is not mock-data only), secure defaults, safe error handling, automated tests with free CI, a container image, and clear documentation. Mock data stays the default provider, so anyone can run the repository with one free LLM key.

A web chat interface built with prompt-kit is part of the plan (see Interactive web UI). It is a separate client in `web/`, so the API scope and contract stay as in the PRD.

## BYOK design and decisions

Every value below is read from environment variables (or a `.env` file locally). The code never contains a key, a model name or a city list that cannot be changed from outside.

| Setting | Default | What it controls |
| --- | --- | --- |
| `LLM_MODEL` | `gemini-3.5-flash-lite` | The model used by all three agents. Other providers go through ADK's LiteLLM wrapper using a model string such as `provider/model-name`. |
| `GOOGLE_API_KEY` | none (required for the default model) | Gemini key from Google AI Studio. For another provider, set that provider's own standard key variable instead. |
| `DATA_PROVIDER` | `mock` | `mock` reads JSON data files; `google_places` calls Google Places API (New). |
| `PLACES_API_KEY` | none | Needed only when `DATA_PROVIDER=google_places`. |
| `MOCK_DATA_DIR` | `data/` | Folder of JSON files with attractions and restaurants per city. Users add their own cities here, with no code change. |
| `APP_ENV` | `development` | In `production` the service refuses to start without `SERVICE_API_KEY`. |
| `SERVICE_API_KEY` | none | Secret checked in the `X-API-Key` header. |
| `REQUEST_TIMEOUT_SECONDS` | `45` | Time limit for one agent run. |
| `RATE_LIMIT` | `30/minute` | Per-key request limit. |
| `ALLOWED_ORIGINS` | none | CORS origins for the client. |

Two small additions to the PRD folder structure keep this clean: `config.py` (reads settings) and `providers/` (one file per data provider, same interface). The two tool signatures, `search_attractions(city, category)` and `find_restaurants(city, cuisine)`, stay exactly as in the PRD. The Tokyo and Paris mock records move into JSON files in `data/`, unchanged.

Defaults assumed (confirmed):

- Repository name `travel-concierge-adk`, public, MIT licence.
- Mock data is the default provider; Google Places is optional.
- Acceptance is tested with Swagger (`/docs`) and curl, because the A2UI client is out of scope.
- Sessions stay in memory, as the PRD allows.

## Mac setup (today, Mon 12 Oct)

No cloud account is needed for development. Everything below is free, and a Google Cloud or hosting account is only opened later by following `production_live_steps.md`.

**Accounts and keys**

1. Sign in to GitHub. Create a public repository `travel-concierge-adk` with an MIT licence and a Python `.gitignore`. In the repository settings, turn on secret scanning and push protection, because the repository is public.
2. Open Google AI Studio and create a free Gemini API key. This is your `GOOGLE_API_KEY`. Free-tier limits apply, and free-tier prompts may be used by Google to improve its products (check the current terms), so never test with private data.
3. Google Places key: optional, needed only for Wednesday's live-data test. Create it then, restrict it to Places API (New), and check the current free allowance before using it.

**Tools on the Mac (Terminal)**

4. Install Apple command line tools: `xcode-select --install`
5. Install Homebrew from brew.sh (copy the one-line installer from that site).
6. Install the tools: `brew install git gitleaks` (Python 3.14 is already installed; check `python3 --version`). `gitleaks` scans your commits for secrets before they reach the public repository.
7. Install the editor: `brew install --cask visual-studio-code`, then add the VS Code Python extension.
8. Docker Desktop is needed from Friday to test the container locally. Check its licence terms for personal use, and install it by Thursday night.
9. Claude Code is optional for coding help; your Claude Pro plan covers it.

**Project skeleton (PRD structure plus `config.py`, `providers/`, `data/`, `tests/`)**

10. Clone the repository and create the environment:

```bash
git clone https://github.com/<your-username>/travel-concierge-adk.git && cd travel-concierge-adk
python3 -m venv .venv && source .venv/bin/activate
mkdir agents providers data tests
touch agents/__init__.py agents/coordinator.py agents/attractions_agent.py agents/dining_agent.py
touch providers/__init__.py config.py main.py .env.example
cp .env.example .env
```

11. Create `requirements.txt` with `google-adk`, `fastapi`, `uvicorn`, `pydantic`, `python-dotenv`, `httpx`, and a `requirements-dev.txt` with `pytest`. Run `pip install -r requirements.txt -r requirements-dev.txt`.
12. Put your real keys only in `.env`. Commit `.env.example` with empty values. Confirm `git status` never shows `.env`.
13. Check: run `uvicorn main:app --reload --port 8000`, open `http://localhost:8000/docs`, and make one Gemini call.

Setup is done when the Swagger page opens, one Gemini call works, and the repository has a first commit with no secrets in it.

For the web UI, also install Node.js (`brew install node`, then check `node -v`) by Tuesday night. The UI is created in the `web/` folder on Wednesday.

## Day-by-day plan

The backend baseline is finished by Tuesday. Wednesday and Thursday are the heaviest days, because they carry both the providers and the web UI. From Friday the work is packaging and documentation only.

| Day | Work | Done when |
| --- | --- | --- |
| Mon 12 Oct | Mac setup, public repository, `.env.example`, secret scanning, `config.py`, and the FastAPI skeleton. Install Node.js by night. | Swagger page opens and one Gemini call works |
| Tue 13 Oct | PRD baseline: both tools reading JSON from `data/` (Tokyo, Paris, generic fallback), both specialists, `TravelCoordinator` with `sub_agents`, `POST /api/chat`, and merging of both specialists' components. | "Plan a day in Tokyo with sightseeing and dinner" returns both `CardList` components locally |
| Wed 14 Oct | Morning: Google Places provider and `LLM_MODEL` switching, with safe fallback on errors. Afternoon: `web/` created with prompt-kit (message thread, input, loader) and the server route that calls the API. | A typed message shows the API reply in the browser, and a real city returns live cards |
| Thu 15 Oct | Backend hardening checklist and unit tests. UI: `CardList` and `TextCard` renderer, starter buttons, error states. GitHub Actions CI for both folders. **Check the cut list tonight.** | CI is green, and the Tokyo prompt shows both card lists in the browser |
| Fri 16 Oct | Dockerfiles for the API and the web app, local container test, `production_live_steps.md` for both, UI polish, and the 20-prompt routing check with the free key. **Feature freeze at end of day.** | Both containers run locally using only environment variables |
| Sat 17 Oct | Fix bugs. Pin exact dependency versions (Python versions and the npm lockfile). README with screenshots or a short demo video and a portfolio write-up. Tag `v1.0.0`. | A fresh clone runs in 10 minutes by following the README |
| Sun 18 Oct | Buffer, final check, and sign-off. No new features. | Sign-off given before the deadline |

## Data providers (Wed 14 Oct)

Data comes from a provider chosen by `DATA_PROVIDER`. The PRD tools call the provider, so the tool names, arguments, `a2ui_surface`, component IDs and item fields stay exactly as in the PRD, and the client sees no difference.

1. **`mock` (default, free).** Reads JSON files from `MOCK_DATA_DIR`. Tokyo, Paris and the generic fallback records move into JSON unchanged. A user adds a city by adding a JSON file, with no code change.
2. **`google_places` (BYOK, optional).** Uses Places API (New) Text Search through `httpx` with `PLACES_API_KEY`. Query examples: "tourist attractions in {city}" and "{cuisine} restaurants in {city}". Request only the fields needed (a field mask) and keep at most 5 items per list.
3. **On any error, timeout or empty result,** the service returns the mock result for that city and says in `agent_text` that these are demo records, never presenting them as live.
4. **Adding another provider** is one new file in `providers/` implementing the same two functions. Users who only configure existing providers need no code change.

| PRD field | Attractions list | Dining list |
| --- | --- | --- |
| `title` | place display name | place display name |
| `type` / `cuisine` | place primary type | place primary type (cuisine) |
| `rating` | rating, as a string | rating, as a string |
| `cost` / `price` | "Not listed" (Places has no ticket price) | price level converted to `$` to `$$$$` |

To verify on Wednesday, because current provider documents were not checked here: exact field names and price-level values in the Places API (New) reference, the current free allowance and per-field pricing, and the Google Maps Platform rules on caching and attribution. Do not add a cache until those rules are read. Test the Places provider with a small number of calls on your own key. In CI it is tested only against saved sample responses, so the public repository needs no key.

## Interactive web UI (Wed 14 – Fri 16 Oct)

Build a small custom chat app with prompt-kit, not LibreChat. The PRD leaves the client out of scope, but a demo anyone can click is what makes this a portfolio project, so the UI is added as a separate client in a `web/` folder of the same repository. The API and its contract stay unchanged.

| Option | What it is | Fit for this project |
| --- | --- | --- |
| LibreChat | A full ChatGPT-style platform. Its setup uses a MongoDB database, and it connects to OpenAI-compatible endpoints. | Low. It shows text and markdown, so our `CardList` cards would not appear as cards unless LibreChat itself is modified. |
| prompt-kit (recommended) | MIT-licensed React, Next.js and Tailwind components on shadcn/ui: message, chat container, prompt input, loader. | High. Little code, full control, and we render the cards ourselves. |
| Official A2UI renderers (Google's A2UI project) | Renderers for Google's own A2UI format, with a catalogue of approved components. | Later. The PRD payload is A2UI-style but simplified. See the next paragraph. |

One caution: Google's A2UI project defines its own message format and component catalogue, while the PRD uses a simpler payload (`a2ui_surface`, `CardList`, `TextCard`). The PRD itself says to verify compatibility with the target client. So the web app renders the PRD payload with a small renderer of our own. An adapter to the official A2UI format is a good follow-up for learning, and is not part of this release.

**What the user sees**

- A chat thread with a message box and a loading indicator.
- Starter buttons, for example "Plan a day in Tokyo with sightseeing and dinner" and "Best sushi in Paris".
- Attraction cards (name, type, rating, cost) and restaurant cards (name, cuisine, rating, price), drawn from the response.
- A visible notice when the answer uses demo records instead of live data.
- Friendly messages for errors and timeouts.
- Stretch, only if time remains: a "Tell me more" button on a card that sends a follow-up message in the same session. There are no booking buttons, because booking is out of scope.

**How it is built**

- The browser talks only to the Next.js server route in `web/`, and that route calls the FastAPI service. This keeps `SERVICE_API_KEY` on the server, because a key placed in browser code would be public in a public repository.
- The web app reads `API_BASE_URL` and `SERVICE_API_KEY` as server-side environment variables at runtime, so changing them needs no rebuild or code change.
- The browser creates a `session_id` for each chat. The user types a place in the message, because the PRD request has no location field.
- It runs locally with `npm run dev`, which is free.

**UI acceptance**

- [ ] The Tokyo sightseeing-and-dinner prompt shows both card lists in the browser.
- [ ] A dining-only prompt shows only restaurant cards.
- [ ] The PRD sample response renders correctly in a unit test, including the `TextCard` fallback.
- [ ] A stopped API shows a friendly error and not a blank screen.
- [ ] Browser developer tools show no API key in any request or file.
- [ ] `npm test` and the build run in CI without keys.

**Cut list if behind at the end of Thursday:** drop the "Tell me more" button first, then the demo-data notice styling. If the UI is still not working by Friday noon, release `v1.0.0` as the API only, and ship the UI as `v1.1.0` after the deadline.

## Production hardening checklist (Thu 15 Oct)

These make the reference code safe to run publicly. They follow the PRD's OPS and API requirements.

- [ ] Startup check: the app refuses to start if the key for the chosen LLM is missing, if `DATA_PROVIDER=google_places` has no `PLACES_API_KEY`, or if `APP_ENV=production` has no `SERVICE_API_KEY`.
- [ ] Public-repository hygiene: no keys in code or history, `.env` ignored, `.env.example` complete, `gitleaks` run before each push, and keys never written to logs.
- [ ] Request limits: `message` is 1 to 2000 characters; `user_id` and `session_id` are at most 64 characters. Field names and defaults stay as in the PRD.
- [ ] Access control: `X-API-Key` is checked against `SERVICE_API_KEY` when set (mandatory in production), with a per-key rate limit from `RATE_LIMIT`.
- [ ] Timeout: the ADK run is wrapped in `REQUEST_TIMEOUT_SECONDS` and returns a clear timeout error.
- [ ] Safe errors: HTTP 500 and timeout responses carry a short message and a correlation ID. Stack traces go only to server logs.
- [ ] Partial results: if one specialist fails, return the other's cards and say what is unavailable. Never invent recommendations.
- [ ] Merge logic: combine components from all specialist responses by component ID, not just the last tool response.
- [ ] Payload check: validate `a2ui_payload` with Pydantic models (`CardList`, `TextCard`) before returning. If invalid or empty, return `fallback_text_card`.
- [ ] Logging: one structured JSON log line per request (correlation ID, user_id, session_id, routing, latency, status).
- [ ] `GET /health` for the host's health checks.
- [ ] CORS limited to `ALLOWED_ORIGINS`.
- [ ] Honest labelling: when mock data is used, say so in `agent_text`.
- [ ] Tests for both tools, both providers, merge logic, fallbacks and validation.

## Deployment readiness and production_live_steps.md (Fri 16 Oct)

Nothing is deployed in this plan. The repository only has to be ready, so that going live later, on Google Cloud Run or any other host, needs no repository code change.

What the repository must contain:

- A `Dockerfile` (`python:3.14-slim` image) that installs `requirements.txt` and starts `uvicorn main:app --host 0.0.0.0 --port $PORT`, plus `.dockerignore`.
- All behaviour set through the environment variables in the BYOK table. No host name, region or cloud service is written anywhere in the code.
- `GET /health` and JSON logs to standard output, which every container host can read.
- `production_live_steps.md`, written so that you or anyone else can follow it without editing code.

Outline of `production_live_steps.md`:

1. **What you need:** a cloud account with billing, the keys you will use, and the cost warning that live Gemini and Places calls are charged.
2. **Set up the cloud account:** project, billing, and the APIs to enable.
3. **Store the keys** as secrets, never in the image. Example for Cloud Run:

```bash
printf '%s' "$GOOGLE_API_KEY" | gcloud secrets create google-api-key --data-file=-
printf '%s' "$SERVICE_API_KEY" | gcloud secrets create service-api-key --data-file=-
```

4. **Deploy** the same image with settings only:

```bash
gcloud run deploy travel-concierge --source . --region <your-region> --allow-unauthenticated \
  --min-instances 1 --max-instances 1 --timeout 60 \
  --set-env-vars APP_ENV=production,DATA_PROVIDER=mock \
  --set-secrets GOOGLE_API_KEY=google-api-key:latest,SERVICE_API_KEY=service-api-key:latest
```

5. **Turn on live data or another model later** by changing only the environment variables (`DATA_PROVIDER`, `PLACES_API_KEY`, `LLM_MODEL`), then redeploying.
6. **Smoke tests** with curl, a **rollback** command, and a **budget alert** step.
7. **Other hosts:** any host that runs a Docker image and sets environment variables works with the same settings.

Minimum and maximum of 1 instance keeps the in-memory sessions consistent. Persistent sessions are the follow-up before real scale.

Check on Friday: every setting named in the file exists in `.env.example`, and the container starts locally using only environment variables.

The web UI is a second small container (`web/Dockerfile`), configured only by `API_BASE_URL` and `SERVICE_API_KEY`. Both are read on the server at runtime, because browser-visible Next.js variables are fixed at build time and would force a rebuild. `production_live_steps.md` covers both services, and any host that runs two containers works.

## Testing and acceptance

The release is accepted when every row passes locally and in the container. Tests marked CI run on GitHub Actions with no keys; tests marked manual use your own free keys.

| Test | Passes when | Where |
| --- | --- | --- |
| Sightseeing only ("What to see in Paris?") | Only `attractions_card_list` is returned | Manual |
| Dining only ("Best sushi in Tokyo") | Only `dining_card_list` is returned | Manual |
| Combined ("Plan a day in Tokyo with sightseeing and dinner") | Both components arrive in one `a2ui_payload` | Manual |
| New city added as a JSON file in `data/` | Its cards appear with no code change | CI |
| Places provider with saved sample responses | Items map to the PRD fields | CI |
| Places failure forced (wrong key) | HTTP 200 with mock cards, labelled as demo records | CI |
| Live Places call on a real city | Real cards are returned | Manual, a few calls only |
| `LLM_MODEL` changed to a second model | The service runs with no code change | Manual |
| No structured output | HTTP 200 with `fallback_text_card` | CI |
| Missing `message` | HTTP 422 | CI |
| Wrong or missing `X-API-Key` | Request rejected | CI |
| `APP_ENV=production` without `SERVICE_API_KEY` | App refuses to start | CI |
| Model call exceeds the time limit | Clear timeout error with a correlation ID, no stack trace | CI |
| Container started with environment variables only | `/health` and a chat request work | Manual |
| Every setting in `production_live_steps.md` | Also exists in `.env.example` | CI |
| 20 representative prompts | Routing checked by hand; the team sets the numeric target (a proposed start is 90% routed correctly) | Manual |

Free Gemini limits can slow the 20-prompt check, so space the requests. Record the Friday results as the baseline, because the PRD asks the team to set numeric targets for routing, latency and errors.

## Risks and fallback plan

The main risk is time: the BYOK design adds a configuration layer to a 7-day plan. Because mock data is the default and live data is optional, no single feature can block the release.

| Risk | Effect | Fallback |
| --- | --- | --- |
| Places provider is not stable by Thursday | Delays the release | Keep `DATA_PROVIDER=mock` as the default and ship the Places provider as marked experimental |
| ADK nested events do not expose both specialist results as expected | Combined requests return only one list | Test this on Tuesday first. Pin the ADK version, and read specialist tool responses explicitly. |
| Non-Gemini models through LiteLLM behave differently with sub-agents and tools | Routing quality drops | Document Gemini as the tested model, and list other models as untested until you try them |
| Free Gemini tier limits or quota changes | Tests fail or slow down | Space test requests, keep CI free of LLM calls, and re-check the current free limits |
| A secret is committed to the public repository | Key must be revoked | Secret scanning, push protection, `gitleaks`, and revoke any key that leaks at once |
| `production_live_steps.md` is wrong when first used | Go-live is delayed | Check every command against the container and `.env.example` on Friday. Treat the first real deploy as a test. |
| Sessions reset on restart (in-memory) | Conversation context lost | Accepted for this release; single instance; persistent sessions are a follow-up |
| Dependencies change (ADK or A2UI conventions) | Surprise breakage | Pin exact versions on Saturday and do not upgrade before the tag |
| Scope creep (booking, itineraries, forms) | Misses the deadline | These stay out of scope, as the PRD says |

Proposed follow-up after `v1.0.0`: persistent sessions, a real A2UI client check, numeric service targets, and Google Places attribution in the client.
