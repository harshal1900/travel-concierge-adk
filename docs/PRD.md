# Smart Travel & Local Experience Concierge — PRD

Product Requirements Document · Smart Travel & Local Experience Concierge

> Note: the sequence diagrams and the structure diagram of the original were garbled in the attached text, so they are left out here. All other text is kept in full.

## 1. Business Context

### 1.1 Product Overview

The Smart Travel & Local Experience Concierge is a multi-agent travel recommendation service for individual travelers and corporate planners who need to discover local attractions, restaurants, and itinerary options through a conversational interface. It uses Google ADK to orchestrate specialized agents, Gemini to interpret requests and coordinate responses, and A2UI declarative payloads to deliver structured UI components instead of unstructured text alone.

The reference implementation is a Python FastAPI service with an asynchronous agent execution flow, mock data sources, and a JSON API that returns agent text alongside a declarative UI payload.

### 1.2 Problem Statement

Travelers must otherwise research sightseeing and dining options across multiple sources and manually combine their findings into a useful plan. Corporate planners face the same fragmentation when assembling local experiences for trips.

The product addresses this problem by accepting a natural-language trip request, routing relevant tasks to specialized agents, and combining their results into a unified response that a compatible client can render as interactive cards.

### 1.3 Target Users and Value

- Individual travelers: Discover attractions and dining options for a destination without issuing separate searches.
- Corporate planners: Gather destination and dining recommendations to support itinerary preparation.
- Client application developers: Consume consistent, declarative A2UI payloads instead of parsing free-form text to construct recommendation interfaces.

The primary value is reduced research effort and a consistent presentation of recommendations from multiple specialized agents.

### 1.4 Business Goals and Success Metrics

The initial release should validate the multi-agent architecture, the quality of intent routing, and the delivery of structured UI responses before investing in live data integrations.

| Goal | Success metric |
| --- | --- |
| Correctly interpret travel requests | Percentage of requests routed to the appropriate specialist or specialists |
| Deliver useful recommendations | Percentage of successful requests returning relevant attraction or dining cards |
| Support combined requests | Percentage of sightseeing-and-dining requests returning a unified response containing both result types |
| Provide reliable API behavior | Request success rate, HTTP 5xx rate, and timeout rate |
| Deliver renderable UI data | Percentage of responses whose A2UI payload conforms to the client-supported schema |
| Maintain responsive interactions | End-to-end latency, including specialist execution and response assembly |

Measurement assumption: The reference implementation does not define numeric service-level objectives, analytics instrumentation, or evaluation datasets. Product and engineering should establish baseline measurements during integration and set numeric targets before production launch. Metrics must distinguish a successful HTTP response from a genuinely useful, correctly structured recommendation.

### 1.5 Scope and Boundaries

In scope

- Natural-language travel request intake through `POST /api/chat`.
- Intent interpretation and delegation by `TravelCoordinator`.
- Attraction discovery through `AttractionsSpecialist` and `search_attractions(city, category)`.
- Dining recommendations through `DiningSpecialist` and `find_restaurants(city, cuisine)`.
- Combination of specialist results into a unified response.
- A2UI `CardList` payloads and a `TextCard` fallback.
- Asynchronous execution through Google ADK's `Runner.run_async`.
- Session handling through `InMemorySessionService`.
- Mock recommendation data for Tokyo and Paris, with generic fallback records for other cities.
- Configuration through `GOOGLE_API_KEY`, loaded from `.env` for local development.

Out of scope for the reference implementation

- Live attraction or restaurant inventory, verified opening hours, and real-time ratings or prices.
- Live reservation availability, booking creation, cancellation, or confirmation.
- Payments, ticket purchases, and transaction processing.
- Guaranteed itinerary feasibility, travel-time calculations, routing, and transportation booking.
- Persistent user profiles, durable conversation history, and cross-session preference storage.
- Authentication, authorization, production-grade analytics, and client-side rendering implementation.

The source overview mentions booking and preference forms as potential A2UI capabilities, but the implemented tools do not provide booking operations. These capabilities are not part of the initial deliverable.

### 1.6 Key Assumptions and Risks

| Area | Assumption or risk | Requirement or mitigation |
| --- | --- | --- |
| Data sources | Specialist tools use mock data, not live provider integrations. | Label or otherwise distinguish demo recommendations from verified live information in any user-facing production client. |
| Model behavior | All three agents use `gemini-2.5-flash`. Model behavior and tool selection can vary. | Evaluate representative requests and handle missing, malformed, or incomplete results. |
| ADK compatibility | Google ADK APIs, event structures, session interfaces, and import paths may evolve. | Pin validated dependency versions for releases and verify API compatibility when upgrading. |
| A2UI compatibility | A2UI conventions and supported component schemas may evolve. | Validate payload shape and supported component types against the target client contract. |
| Session lifecycle | `InMemorySessionService` is process-local and not durable across restarts. | Retain it for the demo; replace it with a suitable persistent session implementation before production if continuity is required. |
| Error handling | The reference endpoint returns HTTP 500 for uncaught exceptions. | Add structured server-side logging, safe error responses, and clear distinction between upstream, orchestration, and validation failures. |
| Aggregation | Tool outputs are not guaranteed to contain every requested result. | Preserve available results and use a text fallback when structured output is absent; do not fabricate missing recommendations. |
| API credentials | `GOOGLE_API_KEY` is required at startup. | Fail fast on missing configuration and use managed secrets in deployed environments. |

### 1.7 Technical Architecture and Shared Infrastructure

The implementation should retain the reference directory structure and responsibilities:

```
travel_agent_project/
├── requirements.txt
├── .env
├── main.py
└── agents/
    ├── __init__.py
    ├── coordinator.py
    ├── attractions_agent.py
    └── dining_agent.py
```

- Python and FastAPI: Provide the HTTP boundary, request validation through Pydantic, asynchronous request handling, and error-to-HTTP mapping.
- Google ADK: Provides `LlmAgent`, specialist delegation, `Runner`, and session management.
- Gemini (`gemini-2.5-flash`): Interprets natural-language intent, selects applicable specialists, and synthesizes results.
- A2UI: Defines declarative response components such as `CardList` and `TextCard`.
- Mock tool backends: Make the prototype demonstrable without external provider dependencies.
- Uvicorn: Serves the FastAPI application; port `8000` is the reference local-development port.
- Pydantic and python-dotenv: Validate request bodies and load local environment configuration.

Shared components should be initialized at the application boundary rather than duplicated across agents. `main.py` owns the FastAPI application, `InMemorySessionService`, and `Runner`; agent modules define their respective agent and tool behavior. All agents share the configured Gemini access and the ADK execution lifecycle. A compatible client is responsible for rendering the returned A2UI payload.

The reference dependency baseline is `google-adk>=0.1.0`, `fastapi>=0.110.0`, `uvicorn>=0.28.0`, `pydantic>=2.0.0`, and `python-dotenv>=1.0.0`. These minimum versions are source-derived, not a production compatibility guarantee. A release should use a validated, reproducible dependency lock and verify current ADK and A2UI interfaces.

## 2. TravelCoordinator

### Role

`TravelCoordinator` is the root agent responsible for interpreting the user's trip request, determining intent, delegating work to specialized agents, and combining their results into a unified A2UI response payload.

It delegates sightseeing, museums, and monuments to `AttractionsSpecialist`, and food, restaurants, and dining recommendations to `DiningSpecialist`. Requests that cover both domains should use both specialists when appropriate.

The coordinator is responsible for presenting a coherent response, but it must not imply that mock recommendations have been verified against live services.

### Technology Stack

| Component | Choice | Rationale |
| --- | --- | --- |
| Agent and model | Google ADK `LlmAgent`, `gemini-2.5-flash` | Interprets natural-language requests and determines which specialists are relevant. |
| Orchestration | Google ADK `sub_agents` | Preserves the reference architecture, in which `attractions_agent` and `dining_agent` are registered as sub-agents of `coordinator_agent`. |
| Execution | Google ADK `Runner.run_async` | Executes the coordinator asynchronously and exposes events for response collection. |
| Session management | `InMemorySessionService` | Associates execution with the supplied `user_id` and `session_id` during prototype use. |
| API boundary | FastAPI `POST /api/chat`, with Pydantic request validation | Provides a stable transport contract independent of internal agent implementation. |
| Model configuration | `GOOGLE_API_KEY` loaded through `python-dotenv` | Supplies Gemini credentials without hardcoding them in agent code. |
| Response format | A2UI declarative payloads | Allows the coordinator's combined recommendations to be rendered as structured client components. |

Module ownership: `agents/coordinator.py` defines `coordinator_agent` and imports the two specialist agents. `main.py` initializes the shared ADK session service and runner. The coordinator should not duplicate specialist lookup logic.

Memory and production considerations: `InMemorySessionService` is sufficient for a single-process demonstration, not durable conversation history. If production requires persistence, use an ADK-compatible persistent session service and define session expiration, ownership, and recovery behavior. The source does not define a production storage backend, so selecting one remains an implementation decision.

Deployment considerations: Run the FastAPI application under Uvicorn with managed secrets, bounded request execution, and structured logs. Multi-worker deployment requires a session strategy compatible with the deployment topology. Verify current Google ADK interfaces and model availability before release.

### Sequence Diagram

The original contains a sequence diagram of the coordinator's main responsibilities (diagram omitted here). Participants: User, FastAPI `/api/chat`, ADK Runner, TravelCoordinator, AttractionsSpecialist, DiningSpecialist, Gemini 2.5 Flash. Flow, in order:

1. User sends `POST /api/chat`.
2. FastAPI calls `run_async(user_id, session_id, content)` on the ADK Runner.
3. The Runner executes the coordinator turn.
4. The coordinator interprets the request and selects specialists (using Gemini).
5. If sightseeing is requested: the coordinator delegates the attraction request and receives attraction results and an A2UI payload.
6. If dining is requested: the coordinator delegates the dining request and receives restaurant results and an A2UI payload.
7. The coordinator synthesizes the available results into a unified response.
8. Coordinator events return to the Runner, which streams events asynchronously to FastAPI.
9. FastAPI extracts text and structured output. If structured A2UI output is available it is used; if absent, a fallback `TextCard` is built.
10. FastAPI returns HTTP 200 with `agent_text` and `a2ui_payload`. On an unhandled execution exception it returns HTTP 500.

Implementation note: The reference implementation collects the runner's events and inspects function responses for dictionary payloads. A2UI responses from multiple specialists must be merged deliberately rather than assuming that the last tool response is the complete result. The diagram expresses the intended unified response; the exact ADK event and function-response behavior must be verified against the pinned SDK version.

## 3. AttractionsSpecialist

### Role

`AttractionsSpecialist` finds local attractions, ratings, and details. It uses `search_attractions(city, category)` to look up places to visit and returns structured A2UI payloads.

The tool provides mock results for Tokyo and Paris and a generic city-center walk fallback for other destinations. The default category is `"sightseeing"`.

The specialist's responsibility is limited to attraction recommendations. It does not own dining discovery, live availability, booking, or itinerary-wide scheduling.

### Technology Stack

| Component | Choice | Rationale |
| --- | --- | --- |
| Agent and model | Google ADK `LlmAgent`, `gemini-2.5-flash` | Interprets attraction-related instructions and uses the registered lookup tool. |
| Orchestration | `TravelCoordinator` through Google ADK `sub_agents` | Keeps sightseeing behavior specialized while allowing the coordinator to combine results with dining recommendations. |
| Tool | `search_attractions(city, category)` | Encapsulates attraction lookup and returns the data required for recommendation cards. |
| Data source | In-memory Python mock dictionary | Provides deterministic demonstration data without external APIs or credentials for an attraction provider. |
| Response format | A2UI `main_view` with a `CardList` component | Returns structured attraction records containing title, type/category, rating, and cost information. |
| Hosting | Agent module imported by the FastAPI application | Keeps tool logic isolated from HTTP request handling and makes future data-source replacement local to the specialist. |

Module ownership: `agents/attractions_agent.py` defines `search_attractions` and the `attractions_agent` instance, named `AttractionsSpecialist`. The tool normalizes city matching with lowercase and whitespace trimming, looks up the mock records, and constructs the `attractions_card_list` component.

Memory and storage: The tool's mock dictionary is the only attraction data source defined in the reference. It has no independent database, durable memory, or provider client. A future live-data adapter should preserve the tool's argument and result contract where practical, while explicitly handling provider errors, stale data, and missing fields.

Deployment considerations: The specialist executes inside the shared ADK runner and FastAPI service; it is not a separate network service. Tool failures must be surfaced to the orchestration layer so the coordinator can handle incomplete results. Model and ADK configuration are shared with the other agents.

### Sequence Diagram

The original contains a sequence diagram (omitted here). Participants: TravelCoordinator, AttractionsSpecialist, Gemini 2.5 Flash, `search_attractions(city, category)`, Mock Attraction Data. Flow:

1. The coordinator delegates the sightseeing request to the specialist.
2. The specialist interprets the request and selects the tool (using Gemini).
3. The specialist calls the tool with city and category.
4. The tool looks up the normalized city in the mock data. For Tokyo or Paris it returns destination-specific attraction records; for another city it returns the generic City Center Walk record.
5. The tool builds a `main_view` `CardList` payload and returns a structured attraction payload.
6. The specialist returns tool result and response, and the coordinator receives the attraction recommendations.
7. If the tool or model fails, an error or unavailable result is returned. The coordinator preserves other available results or uses a fallback.

Payload requirement: The specialist returns `a2ui_surface: "main_view"` and a component with ID `attractions_card_list`, type `CardList`, a city-specific title, and an `items` array. The reference records use the key `type` for attraction classification, while the product overview describes that field as category. Preserve the actual tool field unless an explicit client-schema migration is approved.

## 4. DiningSpecialist

### Role

`DiningSpecialist` manages cuisine recommendations and dining discovery. It uses `find_restaurants(city, cuisine)` to search restaurant options and formats them into A2UI payloads.

The tool provides mock restaurants for Tokyo and Paris and a generic local-bistro fallback for other destinations. The default cuisine is `"local"`.

The specialist recommends dining options; it does not verify real-time restaurant availability or perform reservations, payments, or other transactions.

### Technology Stack

| Component | Choice | Rationale |
| --- | --- | --- |
| Agent and model | Google ADK `LlmAgent`, `gemini-2.5-flash` | Interprets dining-related instructions and invokes the restaurant lookup tool. |
| Orchestration | `TravelCoordinator` through Google ADK `sub_agents` | Allows dining recommendations to participate in combined travel responses without duplicating coordinator logic. |
| Tool | `find_restaurants(city, cuisine)` | Encapsulates restaurant discovery and returns records suitable for dining cards. |
| Data source | In-memory Python mock dictionary | Supplies predictable destination-specific recommendations without a live restaurant provider. |
| Response format | A2UI `main_view` with a `CardList` component | Presents restaurant title, cuisine, rating, and price as structured fields. |
| Hosting | Agent module imported by the FastAPI application | Keeps restaurant lookup separate from transport and shared orchestration infrastructure. |

Module ownership: `agents/dining_agent.py` defines `find_restaurants` and the `dining_agent` instance, named `DiningSpecialist`. The tool normalizes the city key, selects mock records or the generic fallback, and returns the `dining_card_list` component.

Memory and storage: The reference uses an in-memory Python dictionary and defines no persistent dining preferences, restaurant database, or booking store. The specialist should not infer reservation availability from its static recommendations.

Deployment considerations: The dining specialist shares the coordinator's Gemini model access, ADK runner, session service, FastAPI host, and A2UI response contract. Replacing mock data with a live restaurant provider will require a separate decision on API credentials, rate limits, provider attribution, price freshness, and failure handling.

### Sequence Diagram

The original contains a sequence diagram (omitted here). Participants: TravelCoordinator, DiningSpecialist, Gemini 2.5 Flash, `find_restaurants(city, cuisine)`, Mock Restaurant Data. Flow:

1. The coordinator delegates the food or dining request to the specialist.
2. The specialist interprets the request and selects the tool (using Gemini).
3. The specialist calls the tool with city and cuisine.
4. The tool looks up the normalized city in the mock data. For Tokyo or Paris it returns destination-specific restaurant records; for another city it returns the generic Local Bistro record.
5. The tool builds a `main_view` `CardList` payload and returns a structured dining payload.
6. The specialist returns tool result and response, and the coordinator receives the dining recommendations.
7. If the tool or model fails, an error or unavailable result is returned. The coordinator preserves other available results or uses a fallback.

Payload requirement: The specialist returns `a2ui_surface: "main_view"` and a component with ID `dining_card_list`, type `CardList`, a city-specific title, and an `items` array containing `title`, `cuisine`, `rating`, and `price`.

## 5. Cross-Agent Integration and API Contract

### 5.1 End-To-End Collaboration

For a representative request such as "Plan a day in Tokyo with sightseeing and dinner," the system should route the sightseeing intent to `AttractionsSpecialist` and the dining intent to `DiningSpecialist`. `TravelCoordinator` combines the available results, and the FastAPI layer returns the agent text and A2UI payload.

The original contains an end-to-end sequence diagram (omitted here). Participants: Traveler, FastAPI `main.py`, InMemorySessionService, Google ADK Runner, TravelCoordinator, Gemini 2.5 Flash, AttractionsSpecialist, `search_attractions`, DiningSpecialist, `find_restaurants`. Flow:

1. Traveler sends `POST /api/chat`.
2. FastAPI calls `create_session(user_id, session_id)` and then `run_async(user_id, session_id, content)` on the Runner.
3. The Runner executes the trip request through the coordinator, which interprets sightseeing and dinner intents with Gemini.
4. In parallel branches (sightseeing and dining): the coordinator delegates attraction discovery, the specialist selects its tool and calls `search_attractions(Tokyo, sightseeing)` and returns an attraction `CardList` payload; the coordinator delegates restaurant discovery, the specialist selects its tool and calls `find_restaurants(Tokyo, local)` and returns a dining `CardList` payload.
5. The coordinator combines the available results into a unified response (text and structured output).
6. Coordinator response events flow back through the Runner to FastAPI, which extracts the text and selects the A2UI payload.
7. If structured payload is absent, FastAPI constructs a fallback `TextCard` and returns HTTP 200 with the fallback payload. On an unhandled exception it returns HTTP 500.
8. Otherwise it returns HTTP 200 with `agent_text` and `a2ui_payload`.

Implementation assumptions and clarifications

- The diagram shows the intended collaboration, not a guarantee that ADK executes the two specialists concurrently. The reference code does not explicitly configure parallel execution.
- `TravelCoordinator` remains the root agent and the single owner of intent routing and response synthesis.
- Both specialist tools return complete A2UI component payloads. The coordinator or response-assembly layer must combine the component arrays when both are needed.
- The reference implementation extracts structured output from function-response events. Engineering must verify how the pinned ADK version exposes nested specialist events and final coordinator output; it must not assume that an arbitrary tool response is the final merged payload.
- The reference tool records contain ratings and prices but do not contain dates, durations, opening hours, travel times, or booking confirmations. The service must not represent a list of recommendations as a verified, time-feasible itinerary.

### 5.2 HTTP API: `POST /api/chat`

Purpose: Accept a travel-related message, execute `TravelCoordinator` through Google ADK, and return natural-language text with a structured A2UI payload.

Method: POST · Path: /api/chat · Content type: application/json

#### Request Contract

| Field | Type | Required | Reference behavior |
| --- | --- | --- | --- |
| `user_id` | string | No | Defaults to `"demo_user"` |
| `session_id` | string | No | Defaults to `"session_001"` |
| `message` | string | Yes | Natural-language travel request |

The request is validated by the Pydantic `UserQueryRequest` model in `main.py`.

Example:

```json
{
  "user_id": "traveler_1",
  "session_id": "tokyo_trip_1",
  "message": "Plan a day in Tokyo with sightseeing and dinner."
}
```

Assumption: The reference model does not define explicit minimum message length, maximum request size, or field-level validation constraints beyond the declared types and defaults. Production hardening should define these constraints without changing the existing field names.

#### Success Response Contract

The response contains three top-level fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `status` | string | `"success"` for a completed request |
| `agent_text` | string | Text collected from the ADK execution events |
| `a2ui_payload` | object | Structured declarative UI payload or fallback `TextCard` |

Example response:

```json
{
  "status": "success",
  "agent_text": "Here are sightseeing and dining recommendations for Tokyo.",
  "a2ui_payload": {
    "a2ui_surface": "main_view",
    "components": [
      {
        "id": "attractions_card_list",
        "type": "CardList",
        "title": "Top Attractions in Tokyo",
        "items": [
          {
            "title": "Senso-ji Temple",
            "type": "Culture",
            "rating": "4.8",
            "cost": "Free"
          },
          {
            "title": "Tokyo Skytree",
            "type": "Views",
            "rating": "4.6",
            "cost": "$25"
          }
        ]
      },
      {
        "id": "dining_card_list",
        "type": "CardList",
        "title": "Recommended Dining in Tokyo",
        "items": [
          {
            "title": "Ichiran Ramen",
            "cuisine": "Ramen",
            "rating": "4.9",
            "price": "$$"
          },
          {
            "title": "Sukiyabashi Jiro",
            "cuisine": "Sushi",
            "rating": "4.9",
            "price": "$$$$"
          }
        ]
      }
    ]
  }
}
```

The response above illustrates the intended merged payload. It is not a claim that the current event-extraction implementation always produces this exact structure.

#### Error Contract

The reference endpoint maps uncaught exceptions to HTTP 500 with an exception detail in the response. The following handling is recommended without changing the successful response contract:

| Condition | Expected behavior |
| --- | --- |
| Invalid request body | HTTP 422 through FastAPI/Pydantic validation |
| Missing `GOOGLE_API_KEY` | Fail application startup with a configuration error |
| ADK, Gemini, or tool execution exception | HTTP 500 under the reference behavior |
| Structured output absent | Return HTTP 200 with a fallback `TextCard` if agent execution otherwise completes |
| Partial specialist failure | Preserve successful recommendations when safely possible; identify unavailable results rather than inventing data |

Production requirement: Log exception context and correlation identifiers server-side, but do not expose stack traces, credentials, or sensitive internal details in HTTP responses. A stable error response schema and explicit timeout policy are production-hardening additions, not existing reference behavior.

### 5.3 A2UI Payload Structure

The service returns declarative UI data in `a2ui_payload`. A compatible client is responsible for interpreting the payload and rendering the appropriate components.

#### Surface and Component Schema

| Field | Purpose | Reference values |
| --- | --- | --- |
| `a2ui_surface` | Identifies the UI surface receiving the response | `"main_view"` |
| `components` | Ordered array of declarative components | `CardList`, `TextCard` |
| `components[].id` | Component identifier | `attractions_card_list`, `dining_card_list`, `fallback_text_card` |
| `components[].type` | Component type | `"CardList"` or `"TextCard"` |
| `components[].title` | Display title for a list | City-specific attraction or dining heading |
| `components[].items` | Recommendation records for a list | Tool-specific attraction or dining fields |
| `components[].content` | Text content for the fallback card | Collected `agent_text` |

The reference structure (the original shows it as a diagram, omitted here): the `POST /api/chat` response contains `a2ui_payload`, which contains `a2ui_surface: main_view` and `components[]`. The components are a `CardList` with ID `attractions_card_list`, a `CardList` with ID `dining_card_list`, and a `TextCard` with ID `fallback_text_card` used when structured output is absent.

#### Component Data Requirements

Attraction `CardList`

- ID: `attractions_card_list`
- Type: `CardList`
- Title: `Top Attractions in {City}`
- Items: `title`, `type`, `rating`, and `cost`

Dining `CardList`

- ID: `dining_card_list`
- Type: `CardList`
- Title: `Recommended Dining in {City}`
- Items: `title`, `cuisine`, `rating`, and `price`

Fallback `TextCard`

- ID: `fallback_text_card`
- Type: `TextCard`
- Content: collected `agent_text`

The source overview also describes action buttons, itinerary lists, and booking or preference forms as potential A2UI capabilities. They are not implemented by the two current tools and are excluded from this PRD's initial functional requirements.

Schema compatibility assumption: The reference establishes the outer payload keys and component conventions but does not provide a formal A2UI schema, renderer implementation, or versioned validation specification. The team must verify the component definitions against the target A2UI client and introduce schema validation at the API boundary before production deployment.

### 5.4 Implementation and Release Requirements

The following requirements preserve the reference architecture while making the implementation operationally dependable.

| ID | Requirement | Priority |
| --- | --- | --- |
| API-01 | Expose `POST /api/chat` with the documented request fields and defaults. | Must |
| ORCH-01 | Register `AttractionsSpecialist` and `DiningSpecialist` as sub-agents of `TravelCoordinator`. | Must |
| ORCH-02 | Route sightseeing and dining intents to the corresponding specialists. | Must |
| ORCH-03 | Combine available specialist outputs into one coherent response without dropping valid component results. | Must |
| TOOL-01 | Preserve the signatures and responsibilities of `search_attractions(city, category)` and `find_restaurants(city, cuisine)`. | Must |
| TOOL-02 | Preserve Tokyo and Paris mock records and the generic fallback behavior for other cities. | Must |
| UI-01 | Return A2UI `main_view` payloads containing the supported `CardList` components. | Must |
| UI-02 | Return a `TextCard` fallback when structured output is absent but execution succeeds. | Must |
| OPS-01 | Validate required configuration at startup and use environment-based secrets. | Must |
| OPS-02 | Handle asynchronous execution and errors without silently converting failed executions into successful recommendations. | Must |
| OPS-03 | Verify ADK event handling, model configuration, and A2UI schema compatibility against pinned dependencies. | Must |
| PROD-01 | Replace process-local sessions if durable cross-restart or multi-worker continuity is required. | Before production if required |
| PROD-02 | Replace mock recommendation backends before presenting ratings, prices, or availability as current real-world data. | Before live-data launch |

### 5.5 Delivery Boundaries and Decisions

The initial implementation is complete when the FastAPI endpoint can accept a travel request, execute the coordinator and relevant specialist tools through Google ADK, and return agent text with a correctly structured A2UI response or the documented text fallback.

The implementation should retain the existing module boundaries:

- `main.py` owns HTTP transport, request validation, session initialization, runner execution, event extraction, and response construction.
- `agents/coordinator.py` owns the `TravelCoordinator` definition and specialist registration.
- `agents/attractions_agent.py` owns `AttractionsSpecialist` and `search_attractions`.
- `agents/dining_agent.py` owns `DiningSpecialist` and `find_restaurants`.

No separate microservices, alternative orchestration framework, replacement model, or unrelated storage architecture is required for this release. Production data providers, durable session storage, authentication, numeric service-level objectives, and booking capabilities remain explicit follow-on decisions.

Final product decision: Preserve the Python FastAPI, Google ADK, Gemini `gemini-2.5-flash`, and A2UI architecture as the implementation baseline. Prioritize reliable delegation, correct result aggregation, predictable API responses, and schema compatibility before expanding the concierge into a live booking or itinerary-management product.
