# Status

## 2026-04-11

### Completed in `feat/research-file-workflows`

- Reused the existing OpenWebUI file pipeline for `pdf`, `docx`, `xlsx`, `csv`, `txt`, and `md`: loader extraction, chunking, embedding, vector storage, retrieval, and citation source injection remain in the shared chat path.
- Added explicit router support for `deep_research` and `pptx_generation` while preserving manual model override behavior and normal MWS-backed model selection.
- Normalized URL prompts into `type=url` chat file entries so URL summarization and Q&A flow through the same retrieval/citation path as attachments.
- Expanded web research handling with a deep research mode: multi-query expansion, fetched/deduplicated URLs, RAG collection attachment, and a concise cited-answer contract for the answering model.
- Added PPTX generation from the current chat context with sections for title, problem, solution, architecture, demo flow, value, and roadmap; generated presentations are emitted as normal chat file attachments.
- Updated `.env.example` so RAG embeddings point at the MWS/OpenAI-compatible gateway instead of silently defaulting to local model traffic.
- Added router tests for deep research and PPTX routing plus a dependency-light smoke check in `scripts/smoke-research-file-workflows.py`.

### Verification Notes

- `python3 scripts/smoke-research-file-workflows.py`: passed.
- `python3 -m py_compile backend/open_webui/orchestrator/router.py backend/open_webui/orchestrator/research.py backend/open_webui/retrieval/loaders/main.py`: passed.
- `python3 -m py_compile backend/open_webui/utils/middleware.py`: passed.
- `PYTHONPATH=backend python3 -m unittest backend.open_webui.test.orchestrator.test_router`: blocked by missing local dependency `typer`.
- `git commit -m "feat: wire research file workflows"`: created commit `d8167b45c`.
- `git push origin feat/research-file-workflows`: blocked by workstation SSH auth (`Permission denied (publickey)`).
- Live MWS RAG embedding, URL fetch, web search, and deep research verification still require valid `.env` credentials/provider settings.

### Completed in `feat/chat-panel-manual-mode`

- Added a unified orchestration bar directly into the chat composer with `Auto / Manual`, model selector, upload, URL attach, voice, research, memory, memory panel, and safe mode controls.
- Kept the single-chat OpenWebUI flow intact while routing chat requests through `mws/router` and using `metadata.manual_override` for manual model selection.
- Added assistant-side transparency chips for effective mode, resolved model, inferred/returned tool path, memory result, and live streaming state.
- Added a dedicated in-chat memory panel that lists remembered facts, supports per-item deletion, and allows full memory clearing.
- Preserved existing markdown/code/table/citation/image/file rendering while improving chat-level transparency around the response lifecycle.
- Added Cypress smoke coverage for the new unified chat controls and memory panel toggle.

### Final pass in `feat/chat-panel-manual-mode`

- Verified the new UI remains layered on top of the base OpenWebUI chat rendering path instead of replacing it with separate screens.
- Markdown rendering remains covered by the existing OpenWebUI markdown components.
- Code blocks and copy-code remain covered by the existing code block rendering path.
- Table rendering remains covered by the existing markdown/table rendering path.
- Image preview remains covered by existing composer and assistant attachment rendering.
- File chips remain covered by existing composer and assistant attachment rendering.
- Citations/source rendering remains covered by the existing citations rendering path in assistant responses.
- Improved assistant progress transparency: pending responses now show `Routing...`, `Streaming`, and `Memory pending` states until router/tool/memory metadata resolves.
- Memory transparency now distinguishes `Memory disabled`, `Memory pending`, `Memory saved`, and `Memory unchanged`.

### Demo Artifacts

- `demo-assets/ui/01-unified-chat-controls.svg`: unified composer controls preview.
- `demo-assets/ui/02-assistant-transparency.svg`: assistant model/tool/memory/streaming chips preview.
- `demo-assets/ui/03-memory-panel.svg`: in-chat memory panel preview.
- `demo-assets/ui/04-rendering-coverage.svg`: rendering coverage preview for markdown, tables, code, files, images, and citations.

### Verification Notes

- `git diff --check`: passed.
- Local code sanity check confirmed existing OpenWebUI render components still own markdown, code blocks, copy code, tables, image previews, file chips, and citations.
- `npm run check`: not run successfully because `node_modules` is absent and `svelte-kit` is unavailable.
- `npm run build`: not run successfully because `node_modules` is absent.

### Completed in `feat/multimodal-inputs`

- Updated `docs/CONTRACTS.md` with normalized `attachment_hints`, audio-to-text routing, assistant attachment expectations, and multimodal chat paths.
- Added MIME-based attachment hint normalization in the router so audio/image/url/file intent is inferred from uploaded attachment metadata instead of fragile UI-only heuristics.
- Enabled router-assisted coexistence of manual model choice and auto-routing by sending `manual_override` plus `attachment_hints` from the unified chat payload.
- Tightened image-understanding handling so non-vision manual model selections fail softly with a clear chat error instead of silently attempting an unsupported request.
- Kept microphone input and audio file upload inside the single chat UX and preserved the shared chat pipeline behavior:
  `microphone/audio upload -> ASR -> text -> normal chat completion`.
- Enriched generated-image attachments so image generation/edit flows return full chat attachments instead of bare URLs.
- Expanded `.env.example` with MWS-friendly STT/image-generation settings so multimodal config remains env-driven.
- Added router integration coverage for attachment hints and manual vision rejection.
- Added demo assets in `demo-assets/multimodal/`.
- Added a lightweight dependency-free multimodal wiring smoke check in `scripts/smoke-multimodal-contract.py`.

### Explicit End-to-End Path Check

- Audio file upload path exists: uploaded `audio/*` or `video/*` attachments are marked as audio, routed through ASR/transcription, then continued through the normal text chat path.
- Microphone recording path exists: browser recording goes through transcription and inserts the returned text into the existing composer and chat submit flow.
- Image understanding path exists: image uploads stay in the normal composer flow, are serialized as multimodal parts, and route to a vision-capable model or return a clear non-vision manual-model error.
- Image generation path exists: generation prompts route to image generation and return as assistant attachments inside the same chat.
- MIME adapter influence is explicit: frontend hints are sent in `metadata.attachment_hints`, backend merges/infer hints from files, and router classification consumes those hints before selecting `audio`, `vision`, `file`, or `url`.
- Graceful degradation is implemented for missing vision support and ASR preparation/transcription failures.

### Capability / Access Check

- Live MWS capability discovery was attempted against `https://api.gpt.mws.ru/v1/models`.
- The endpoint responded with `401 Authentication Error, No api key passed in.`, so a real capability matrix could not be fetched from this worktree without credentials.
- Live ASR access was also checked against `https://api.gpt.mws.ru/v1/audio/transcriptions` and returned the same `401` auth error.
- Live image generation access was checked against `https://api.gpt.mws.ru/v1/images/generations` and also returned `401`.
- Result: network reachability is confirmed, but real MWS model/ASR/image capability verification remains blocked on a valid MWS API key in `.env`.

### Verification Notes

- `python3 -m compileall ...`: passed for changed backend routing/multimodal files.
- `python3 scripts/smoke-multimodal-contract.py`: passed.
- `git diff --check`: passed.
- `curl -i https://api.gpt.mws.ru/v1/models`: reached MWS and returned `401` without API key.
- `curl -i -X POST https://api.gpt.mws.ru/v1/audio/transcriptions`: reached MWS and returned `401` without API key.
- `curl -i -X POST https://api.gpt.mws.ru/v1/images/generations`: reached MWS and returned `401` without API key.
- `PYTHONPATH=backend python3 -m unittest ...`: blocked by missing local dependency `typer`.
- `npm run check`: blocked because local frontend dependency tooling is not installed.

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
- UI and multimodal stages reuse the documented contract rather than introducing incompatible API changes.

### Verification Notes

- `bash ./scripts/check-no-secrets.sh`: passed
- `bash -n scripts/check-no-secrets.sh scripts/smoke.sh`: passed
- `git diff --check`: passed
- `docker compose --env-file .env config`: passed with a temporary local `.env`
- `python3 -m compileall ...`: passed for changed backend routing files
- Local `make up` could not complete in this workstation session because the Docker daemon was not available
- `pytest` and fuller backend import-time smoke were not completed because local Python dependencies such as `pytest` and `typer` were missing

### Next Useful Steps

- Finish this merge into `develop`.
- Rehearse the chat + multimodal happy path with a real `.env` and pinned MWS model IDs.
- Launch the research/file/PPTX agent on top of the merged `develop`.
- Expand smoke coverage from auth/chat shell into one real credentialed multimodal completion flow.
- Decide whether SQLite remains enough for demo/release or whether Postgres becomes a required profile later.
