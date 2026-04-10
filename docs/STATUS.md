# Status

## 2026-04-11

### Completed in `feat/multimodal-inputs`

- Updated `docs/CONTRACTS.md` before the multimodal API changes with normalized `attachment_hints`, audio-to-text routing, and assistant attachment expectations.
- Added MIME-based attachment hint normalization in the router so audio/image/url/file intent is inferred from uploaded attachment metadata instead of fragile UI-only heuristics.
- Enabled router-assisted coexistence of manual model choice and auto-routing by sending `manual_override` plus `attachment_hints` from the unified chat payload.
- Tightened image-understanding handling so non-vision manual model selections fail softly with a clear chat error instead of silently attempting an unsupported request.
- Kept microphone input and audio file upload inside the single chat UX and preserved the shared chat pipeline behavior:
  `microphone/audio upload -> ASR -> text -> normal chat completion`.
- Enriched generated-image attachments so image generation/edit flows return full chat attachments (`id`, `name`, `content_type`, `url`) instead of bare URLs.
- Expanded `.env.example` with MWS-friendly STT/image-generation settings so multimodal config remains env-driven.
- Added router integration coverage for attachment hints and manual vision rejection.
- Added demo assets in `demo-assets/multimodal/` for audio and image smoke checks in the unified chat.

### Capability / Access Check

- Live MWS capability discovery was attempted on 2026-04-11 against `https://api.gpt.mws.ru/v1/models`.
- The endpoint responded with `401 Authentication Error, No api key passed in.`, so a real capability matrix could not be fetched from this branch workspace without credentials.
- Live ASR access was also checked on 2026-04-11 against `https://api.gpt.mws.ru/v1/audio/transcriptions` and returned the same `401` auth error.
- Live image generation access was checked on 2026-04-11 against `https://api.gpt.mws.ru/v1/images/generations` and also returned `401`.
- Result: network reachability is confirmed, but real MWS model/ASR/image capability verification remains blocked on a valid MWS API key in `.env`.

### Contract Check

- Multimodal request/response changes were documented first in `docs/CONTRACTS.md`.
- The implementation keeps everything inside the existing chat surface and reuses the shared chat pipeline instead of introducing separate modality-specific screens.

### Verification Notes

- `python3 -m compileall backend/open_webui/orchestrator/router.py backend/open_webui/routers/images.py backend/open_webui/utils/middleware.py backend/open_webui/test/orchestrator/test_router.py`: passed
- `git diff --check`: passed
- `curl -i https://api.gpt.mws.ru/v1/models`: reached MWS and returned `401` without API key
- `curl -i -X POST https://api.gpt.mws.ru/v1/audio/transcriptions`: reached MWS and returned `401` without API key
- `curl -i -X POST https://api.gpt.mws.ru/v1/images/generations`: reached MWS and returned `401` without API key
- `PYTHONPATH=backend python3 -m unittest open_webui.test.orchestrator.test_router`: could not run because local dependency `typer` is missing
- `npm run check`: could not run because local frontend dependency tooling is not installed (`svelte-kit: command not found`)

## 2026-04-10

### Completed in `chore/infra-release-readme`

- Rebuilt `.env.example` around safe placeholders and MWS GPT as the default model gateway.
- Added secret-discipline validation in `scripts/check-no-secrets.sh`.
- Standardized the local startup path around `make up`, `make smoke`, `make logs`, and `make down`.
- Wired `docker-compose.yaml` to load `.env` and pass the MWS/OpenAI-compatible settings into Open WebUI.
- Added shell smoke coverage for `/health`, signup, and signin.
- Added minimal Cypress smoke coverage to verify auth lands in the unified chat flow.
- Replaced the generic upstream README with project-specific run/demo instructions.
- Filled architecture, feature matrix, blockers, and demo docs for release coordination.
- Prepared a single CI workflow for lint, backend smoke tests, and frontend smoke.

### Completed in `feat/openwebui-routing-memory`

- Added an MWS-backed orchestration layer for OpenWebUI backend with an explicit virtual router model `mws/router`.
- Default OpenAI-compatible backend now falls back to `MWS_BASE_URL` and `MWS_API_KEY` when `OPENAI_*` env vars are unset.
- Implemented capability inference/registry for text, vision, audio, embeddings, and image generation models.
- Added backend orchestrator endpoints for model sync and router decision preview.
- Integrated routing into the existing chat path without replacing the single-chat UX:
  `text -> text llm`, `audio -> asr preprocessing`, `image + question -> vlm`, `draw/generate image -> image generation`, `file -> file qa`, `url -> url parse`, `search/latest/research -> web research`.
- Extended long-term memory records with `kind`, `source`, and `enabled`, plus user memory preferences for opt-in/opt-out.
- Added router smoke tests and verified changed backend files with `python3 -m compileall`.
- Added project contracts and handoff notes in `docs/CONTRACTS.md`.

### Contract Check

- Shared backend contracts are now documented in `docs/CONTRACTS.md`.
- Infra/docs stage did not change API shape, but routing/memory stage introduced and documented orchestration and memory contracts.
- Agents 2–4 should now use `docs/CONTRACTS.md` as the source of truth before implementing UI, multimodal, and tools flows.

### Verification Notes

- `bash ./scripts/check-no-secrets.sh`: passed
- `bash -n scripts/check-no-secrets.sh scripts/smoke.sh`: passed
- `git diff --check`: passed
- `docker compose --env-file .env config`: passed with a temporary local `.env`
- `python3 -m compileall ...`: passed for changed backend routing files
- Local `make up` could not complete in this workstation session because the Docker daemon was not available
- `pytest` and full backend import-time smoke were not completed because local Python dependencies such as `pytest` and `typer` were missing

### Next Useful Steps

- Merge these foundations into `develop` and use them as the baseline for Agents 2 and 3.
- Validate the exact MWS model IDs the demo should pin in `DEFAULT_MODELS` and `TASK_MODEL`.
- Launch frontend/manual-mode work on top of `docs/CONTRACTS.md`.
- Launch multimodal work with an early capability check for Whisper, VLM, and image generation paths.
- Extend smoke coverage from auth/landing into one real chat completion in an environment with demo credentials.
- Decide whether SQLite remains enough for demo/release or whether Postgres becomes a required profile later.
