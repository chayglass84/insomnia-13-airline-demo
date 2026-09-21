# Insomnia Airlines Demo

A self-contained Insomnia workspace for demoing Insomnia and Kong together. It's built around a fictional airline, **Insomnia Airlines**, and pairs a set of "real" domain APIs (flights, bookings, baggage, operations) with a set of collections designed to show off specific Insomnia and Kong platform features.

This repo is Insomnia documents only (`.yaml` exports, git-sync format). The backing API implementation lives separately at **[insomnia-airlines-api](https://github.com/chayglass84/insomnia-airlines-api)** — clone that if you want to run the API locally; otherwise the Staging and Production environments below point at already-running instances. Note Staging is deployed to a free server that takes about 45 seconds to respond to the first request, and Prod just wraps Staging in a simple API Gateway. 

## Environments

Every domain collection ships with the same three environments. Switch between them in Insomnia's environment picker (top left) — same requests, different `base_url`.

| Environment | `base_url` | What it's actually hitting | Setup |
|---|---|---|---|
| Dev | `http://localhost:8000` | The API running locally | Clone [insomnia-airlines-api](https://github.com/chayglass84/insomnia-airlines-api) and run it per that repo's instructions before sending requests. |
| Staging | `https://insomnia-airlines-api.onrender.com` | The same API, hosted on Render | Works out of the box — no local setup. Render's free tier spins down when idle, so the **first request after a while takes ~45 seconds** to cold-boot. Don't be alarmed by the delay live in front of a customer; just narrate it, or fire a throwaway request before the call starts. |
| Production | A Kong-managed serverless gateway URL (`*.us.serverless.gateways.konggateway.com`) | The Render-hosted API, fronted by **Kong Gateway** | Works out of the box, but this URL currently points at the demo author's own Konnect org/gateway. If you want your own Kong Gateway in front of the API instead, grab a **Konnect Personal Access Token** for your own org and stand up an equivalent Cloud Gateway — see the CI section below for where a Konnect PAT is also needed. |


## Domain APIs

These four collections model the actual airline domain and correspond directly to the endpoints in the [insomnia-airlines-api](https://github.com/chayglass84/insomnia-airlines-api) repo. Good for general "here's a realistic API surface" walkthroughs, contract testing, or as raw material for other Kong demos (rate limiting, transformations, etc. on top of a real-looking spec).

- **Flights** — airports, flights, and routes. Each collection doc wraps a full OpenAPI 3.0 spec (visible under the `spec` key) in addition to the runnable requests, and that spec is what the GitHub Action below publishes to Konnect.
- **Bookings** — bookings (PNR-based), seat assignments, passengers, frequent-flyer lookups.
- **Operations** — four sub-folders covering ground/ops-side systems: Rewards (miles credit/redeem), Catering (manifests), Mechanics (work orders — note the `Idempotency-Key` header on "Create work order," a nice one to point out), and Aircraft (fleet/tail number status).
- **Baggage** — bag check-in, tracking events, lost-baggage cases. Also the home of the auth walkthrough below, so it does double duty as a platform-feature demo.

## Platform Feature Demos

These collections exist to demonstrate specific Insomnia/Kong capabilities rather than to be a complete API. Each is small and self-contained.

### Baggage — Contains demos for scripts, folder-level scripts, template tags, request chaining and native vault integrations. 

Three ways to attach a bearer token
The `bags` folder description (visible in the Insomnia UI) is a full write-up, but the short version: it shows the **same token**, obtained from `GET /auth/token`, attached three different ways so you can pick the right pattern for a given demo:

1. **Auth tab, response template tag** (`List bags (auth tab)`) — the token field uses `{% response 'body', '<req-id>', ... %}`, Insomnia's built-in response-chaining tag. No script involved; auth is visible in the UI. Best when transparency matters.
2. **Pre-request script, programmatic header** (`List bags on a booking (script auth)`) — a pre-request script calls `insomnia.sendRequest()` to fetch a fresh token and adds `Authorization` via `insomnia.request.addHeader()`. Use this when you need runtime logic (conditional fetch, caching, environment-aware schemes).
3. **Response template tag directly in a header** (`List bags on a flight (template tag)`) — same chaining tag as #1, but pasted as a raw header value instead of using the Auth tab. Also stacks a second trick: a pre-request script that seeds `flight_number`/`departure_date` globals from `GET /bookings` the first time you send, so you don't need to hand-fill path params before your first request.

That same request also has a `{% vault 'aws', ... %}` tag on a header — a live example of Insomnia's **Vault** integration for pulling secrets at request time, worth flagging if the customer cares about secret management.

### Security & Testing
A grab-bag of platform mechanics, useful individually:
- **Inheritance Test** — Basic auth username set to `{{ _.inherited_value }}`, demonstrating variable resolution across scopes (pair with the dedicated Variable Inheritance collection below for the full story).
- **Delayed response with prompt** — uses `{% prompt 'How many milliseconds?', ... %}`, Insomnia's interactive prompt tag, to ask the user for input at send time.
- **Contains Secret** — another `{% vault 'aws', ... %}` example, this time injecting a secret into a request body.
- **Massive Response** — an endpoint for pulling a large, configurable-size payload; handy for demoing how Insomnia (or a Kong plugin) handles bigger responses.

### Variable Inheritance
A minimal, three-level nested-folder collection (`grandparent` → `parent` → request) where each level can define `test-value`, and the leaf request reads `{{ _['test-value'] }}`. Clean way to show scope precedence (request < folder < parent folder < collection < environment) without any domain complexity getting in the way.

### Special Characters
Six folders stress-testing how Insomnia and downstream systems handle unusual input: JSON bodies, URLs/query params/paths, headers/cookies, form and multipart bodies, template-tag edge cases (folder 5 is literally named "the actual gotcha"), and response handling. Good for "does your gateway/plugin mangle this" conversations.

### Linting Bookings + Spectral rulesets
The same Bookings spec, but with deliberately broken conventions (`create_booking` and `PatchBooking` instead of camelCase, etc.), paired with a Spectral ruleset extending `spectral:oas` plus custom rules (required summaries, required 4xx responses, security scheme references, camelCase `operationId`, schema/tag descriptions). Use this pair to demo **spec governance** — linting a spec before it ever reaches a gateway. There are two copies of the same ruleset in the repo root: `.spectral.yaml` for running Spectral from the CLI/CI, and `spectral-insomnia-airlines.yaml` for Insomnia's built-in spec linter to pick up when you open the Linting Bookings spec in the app.

### Collection Runner + Collection Run with Data
- **Collection Runner Example** — ten requests named `01 Request`…`10 Request` with intentionally scrambled `sortKey`s, each hitting a configurable delay endpoint with a passthrough test assertion. Built purely to demonstrate the Collection Runner executing requests in the correct order regardless of collection-view sort order.
- **Collection Run with Data** — a single Flights request driven by `Sheet1.csv` (origin/destination pairs) via the Collection Runner's data-file feature. CSV headers must match environment variable names — that's the one gotcha worth calling out live.

### MCP Flights
Easiest to demo against Huggingface (http://huggingface.co/) or Notion (https://mcp.notion.com/mcp). Notion in particular supports DCR, which is a nice demo.

Can also demo with what's here: An MCP client request pointed at `/mcp` on the **Production** (Kong Gateway) URL, using streamable-HTTP transport. This is talking to Kong's **MCP Proxy Plugin**, which exposes the Flights API as MCP tools — a strong "turn any REST API into an MCP server with Kong" demo. Must be run against Production; Dev/Staging don't have the plugin in front of them.

## CI: Publishing the Flights spec to Konnect
`.github/workflows/deploy-flights-to-konnect.yml` triggers on any push to `flights.yaml` on `master`. It extracts the embedded OpenAPI spec (`.github/scripts/extract_openapi_spec.py`) and publishes it as a new version in the **Kong Konnect API Catalog**, creating the API entry if it doesn't already exist. Worth showing as a "docs/spec as code" story — edit the spec in Insomnia, commit, and Konnect's catalog stays current automatically. (The workflow file also has a commented-out note on why `decK` doesn't substitute for this — decK manages Gateway config, not the API Catalog.)

Needs a `KONNECT_TOKEN` repo secret to run; not required for anything else in this repo. That secret is a Konnect Personal Access Token tied to the demo author's org — if you fork this repo and want the workflow to publish into *your* Konnect org's API Catalog, generate your own PAT and set it as `KONNECT_TOKEN` on your fork.

## Suggested demo flow
1. **Flights / Bookings / Operations** — establish the domain with straightforward CRUD requests, in the Production environment to show Kong Gateway sitting in front of a real API.
2. **Baggage** — walk through the three auth patterns and the Vault-backed header; this is the strongest single "look what Insomnia can do" moment.
3. **MCP Flights** — same Production API, now exposed as MCP tools via Kong's MCP Proxy Plugin.
4. **Linting Bookings** — spec governance with Spectral before anything ships.
5. **Variable Inheritance / Security & Testing / Special Characters** — pull from these as needed for whatever specific mechanic (scoping, prompts, secrets, edge-case payloads) the audience cares about.
6. **Collection Runner / Collection Run with Data** — wrap up with automated, data-driven execution across the requests you just showed.

## Prerequisites
- A recent Insomnia release (collections were authored against `12.5.1-alpha.0`; anything reasonably current should open them fine).
- For the Vault-backed requests (in Baggage and Security & Testing) and the Konnect CI workflow, the relevant Kong Vault / Konnect credentials need to be configured — those are environment/account-level, not stored in this repo.
- For MCP Flights, the target Kong Gateway instance needs the MCP Proxy Plugin enabled on the Flights service.
- Insomnia has native Konnect integration — add your own organization from the org switcher in the top-left, using a Konnect PAT. Connecting your own org (rather than borrowing the demo author's) is the easiest way to show the Insomnia ⇄ Konnect relationship live, since you can then show specs/gateways landing in an org the audience knows is yours.
