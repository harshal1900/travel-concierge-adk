# CLAUDE.md

## Project purpose
- Build **Smart Travel & Local Experience Concierge**: a conversational travel-recommendation app with a Python/FastAPI + Google ADK backend and a separate web chat client in `web/`.
- Read `README.md`, `docs/`, `PRD.md` if present, and the relevant code before changing behavior. The PRD and delivery plan define intended behavior; inspect the repository to determine what is actually implemented.
- Keep changes small, focused, and consistent with the existing project. Do not assume planned files or features already exist.

## Architecture and ownership
- Backend: Python 3.14, FastAPI, Pydantic, Uvicorn, Google ADK, Gemini. The reference model is `gemini-3.5-flash-lite`; model selection should be configurable.
- `main.py` owns HTTP routes, request validation, ADK session/runner lifecycle, event extraction, payload assembly, and HTTP error mapping.
- `agents/coordinator.py` owns `TravelCoordinator` and registration of both specialists.
- `agents/attractions_agent.py` owns `AttractionsSpecialist` and `search_attractions(city, category)`.
- `agents/dining_agent.py` owns `DiningSpecialist` and `find_restaurants(city, cuisine)`.
- `providers/` owns data-provider implementations; `data/` owns mock JSON records; `config.py` owns environment-backed settings. Follow existing names if the repository has already established a different layout.
- `web/` is a separate Next.js/React client. Keep UI-specific code there; do not move backend agent logic into the browser.
- Keep the backend API contract stable when implementing the web UI. If a contract change is truly necessary, explain it first and update tests and documentation together.

## Backend behavior and API contract
- Preserve `POST /api/chat`. Request JSON fields are `user_id` (default `demo_user`), `session_id` (default `session_001`), and required `message`.
- Successful responses contain `status`, `agent_text`, and `a2ui_payload`.
- `a2ui_payload` uses `a2ui_surface: "main_view"` and an ordered `components` array.
- Preserve component IDs and types:
  - Attractions: ID `attractions_card_list`, type `CardList`, title `Top Attractions in {City}`, item fields `title`, `type`, `rating`, `cost`.
  - Dining: ID `dining_card_list`, type `CardList`, title `Recommended Dining in {City}`, item fields `title`, `cuisine`, `rating`, `price`.
  - Fallback: ID `fallback_text_card`, type `TextCard`, field `content` containing the response text.
- Preserve the tool signatures `search_attractions(city, category)` and `find_restaurants(city, cuisine)`. Do not rename their arguments or change the established result fields without an explicit, documented migration.
- `TravelCoordinator` is the single owner of intent routing and response synthesis. Route sightseeing, museums, and monuments to `AttractionsSpecialist`; route food, restaurants, and dining to `DiningSpecialist`; use both when a request asks for both.
- Merge component arrays from all relevant specialist results by component ID. Never assume the last ADK function response contains the complete answer. Verify event behavior against the installed, pinned ADK version.
- If one specialist fails, preserve the other specialist's valid results when possible and clearly state what is unavailable. Never fabricate recommendations or silently turn a failed execution into a successful result.
- If execution succeeds but structured output is missing or invalid, return a validated `TextCard` fallback. Validate response payloads at the API boundary.
- Keep sessions in `InMemorySessionService` for this release unless the user explicitly requests persistent storage. Document that in-memory sessions reset on restart and are process-local.

## Data and truthfulness
- `DATA_PROVIDER=mock` is the default. Mock data must work without a Places API key.
- Preserve Tokyo and Paris sample records and generic-city fallback behavior unless a deliberate data migration is requested.
- Optional `google_places` integration uses Places API (New) through the provider layer and `PLACES_API_KEY`. Keep provider-specific logic out of agent prompts and the HTTP route.
- Provider errors, timeouts, or empty results may fall back to mock data only when the response clearly labels those results as demo records in `agent_text` or the UI.
- Never present mock ratings, costs, prices, opening hours, or availability as verified live facts. Do not invent opening hours, travel times, itinerary feasibility, booking status, or reservations.
- Follow Google Places attribution, field-mask, caching, and pricing requirements before shipping or changing the live provider. Do not add caching without checking applicable rules.

## Web UI rules
- Build a small custom chat UI with Next.js, React, Tailwind, and prompt-kit components where they fit the existing setup. Do not replace it with a full chat platform.
- Keep the browser talking to a Next.js server route; that route calls FastAPI. Do not call the backend directly from browser code when it would expose `SERVICE_API_KEY`.
- Read `API_BASE_URL` and `SERVICE_API_KEY` only in server-side runtime code. Never use `NEXT_PUBLIC_` for secrets. Never return the service key in JSON, HTML, client props, logs, or error messages.
- Create a `session_id` per chat and reuse it for messages in that chat. The request schema has no dedicated destination field; destination belongs in the user's message.
- Render the PRD's simplified payload with a small, explicit renderer for `CardList` and `TextCard`. This payload is A2UI-style, not necessarily the official Google A2UI wire format; do not claim compatibility or add an official-format adapter unless requested.
- Render attraction fields `title`, `type`, `rating`, `cost`; render dining fields `title`, `cuisine`, `rating`, `price`. Handle missing optional values safely and never crash on an unknown component type.
- Include loading and disabled-submit states, friendly API/network/timeout errors, an empty state, and starter prompts. Preserve readable text and keyboard-accessible controls.
- Clearly distinguish demo/mock results from live-provider results when that information is available. Do not add booking, payment, reservation, or ticket-purchase actions; they are out of scope.
- Keep the UI responsive and accessible: semantic elements, visible focus, labels for inputs, adequate contrast, and useful mobile layouts. Do not rely on color alone to communicate status.

## Configuration and security
- Keep secrets out of source, fixtures, screenshots, tests, logs, and commits. Use `.env` locally and commit only safe placeholders in `.env.example`.
- Never print API keys or authorization headers. Redact credentials and sensitive request data from logs and errors.
- Read configuration through the project's settings/config module rather than scattering direct environment lookups across business logic.
- Keep `SERVICE_API_KEY` server-side. When configured, the backend checks `X-API-Key`; in production it is required. Do not weaken auth or CORS to make local development easier.
- Limit CORS to configured `ALLOWED_ORIGINS`. Apply request validation, bounded timeouts, and configured rate limits consistently.
- Return concise, safe client errors with correlation IDs where implemented; keep stack traces in server logs only.
- Do not add cloud-provider-specific assumptions to application logic. Deployment configuration belongs in environment variables and deployment documentation.

## Code quality and dependencies
- Prefer typed Python functions, Pydantic models for external data, small React components, and clear module boundaries.
- Avoid unnecessary abstractions, duplicate agent/provider logic, unrelated refactors, and new dependencies without a concrete need.
- Do not upgrade Google ADK, Next.js, React, or A2UI-related packages casually. Verify compatibility, update the appropriate lock/requirements files, and run the relevant tests/build.
- Follow the repository's existing formatter, lint rules, naming, and package manager. If not established, inspect project configuration before choosing a tool or command.
- Treat external model output and provider responses as untrusted data. Validate shapes before rendering or returning them; do not render raw HTML from model output.

## Tests and verification
- Add or update tests for every behavior change. Keep CI tests deterministic and free of real Gemini/Places calls; use mocks or saved provider responses.
- Backend tests should cover specialist tool schemas, Tokyo/Paris/generic data, provider fallback, coordinator result merging, payload validation, and API error paths as relevant.
- Web tests should cover both `CardList` variants, `TextCard` fallback, unknown/malformed components, loading/error states, and session reuse as relevant.
- Before finishing, run the relevant test suite and production build using scripts actually defined by the repository. Report commands run and any failures; do not claim checks passed if they were not run.
- For end-to-end sanity checks, a combined Tokyo sightseeing-and-dinner prompt should render both card lists; a dining-only prompt should render only dining cards.
- Do not make automated tests depend on a live API key, network service, or quota.

## Working agreement
- Before editing, inspect `git status` and preserve unrelated user changes. Never discard or overwrite user work.
- Search for existing implementations before adding new ones. Prefer editing the source of truth over adding parallel implementations.
- If requirements conflict, prioritize the PRD/API contract, then existing tested behavior; call out any ambiguity rather than silently changing semantics.
- Update README/setup docs and `.env.example` when configuration, commands, or user-visible behavior changes.
- Do not add booking, payments, persistent profiles, durable sessions, real-time itinerary scheduling, or unrelated features unless explicitly requested.
- Keep this file concise and update it only when stable project-wide conventions change.
