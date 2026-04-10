# AI Workspace on Open WebUI Fork

Unified AI workspace for the hackathon team on top of Open WebUI/Fork: one chat UX, model routing, memory, multimodal flows, file/web/research workflows, and a one-command local start.

The operational default for this repo is:
- keep the main Open WebUI chat flow intact
- route model traffic through MWS GPT
- keep manual model selection and future auto-routing compatible
- make startup and demo reproducible without local magic

## Prerequisites

- Docker Desktop or Docker Engine with Compose v2
- `make`
- Node.js 22.x and npm
- Python 3.11
- A valid MWS GPT API key

## Setup

1. Create the local environment file:

   ```bash
   cp .env.example .env
   ```

2. Set the required secrets in `.env`:

   ```dotenv
   OPENAI_API_KEY=<your-mws-gpt-key>
   WEBUI_SECRET_KEY=<random-long-secret>
   ```

3. Optional: pin default chat models for the demo:

   ```dotenv
   DEFAULT_MODELS=mws-gpt-1,mws-gpt-2
   TASK_MODEL=mws-gpt-1
   TASK_MODEL_EXTERNAL=mws-gpt-1
   ```

## Run

One-command local start:

```bash
make up
```

Useful follow-ups:

```bash
make ps
make logs
make smoke
make down
```

The app is available at [http://localhost:3000](http://localhost:3000) by default.

## Environment

The repo keeps committed configuration in `.env.example` and real secrets only in `.env` or CI secrets.

Key variables:
- `OPENAI_API_BASE_URL`: defaults to `https://api.gpt.mws.ru/v1`
- `OPENAI_API_KEY`: required MWS GPT key
- `ENABLE_OPENAI_API`: keeps OpenAI-compatible provider enabled
- `ENABLE_OLLAMA_API`: disabled by default for the hackathon path
- `DEFAULT_MODELS`: preserves manual model selection in the unified chat
- `TASK_MODEL` / `TASK_MODEL_EXTERNAL`: reserved for routing and task helpers
- `WEBUI_SECRET_KEY`: required for stable auth/session behavior
- `OPEN_WEBUI_PORT`: host port, defaults to `3000`

Secret discipline:
- never commit populated `.env`
- never paste keys into docs, screenshots, issues, or PR comments
- rotate any credential immediately if it was exposed
- run `make check-secrets` before pushing infra/doc changes

## Demo Flow

1. Run `make up`.
2. Wait for containers to become healthy, then run `make smoke`.
3. Open `http://localhost:3000`.
4. Create the first admin account.
5. Confirm the user lands in the main chat screen, not a separate workflow screen.
6. Open model selection and verify MWS-backed models are visible.
7. Send a short message from the main chat input.
8. Verify the answer arrives in the same chat thread and the session persists after refresh.

## CI

GitHub Actions covers:
- secret discipline check for `.env.example`
- frontend lint and typecheck
- backend lint and targeted pytest smoke
- container startup plus frontend smoke through Cypress

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/FEATURE_MATRIX.md](docs/FEATURE_MATRIX.md), [docs/DEMO_CHECKLIST.md](docs/DEMO_CHECKLIST.md), and [docs/RELEASE.md](docs/RELEASE.md) for the release/demo baseline.
