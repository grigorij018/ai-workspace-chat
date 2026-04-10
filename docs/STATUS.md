# Status

## 2026-04-11

### Completed in `feat/chat-panel-manual-mode`

- Added a unified orchestration bar directly into the chat composer with `Auto / Manual`, model selector, upload, URL attach, voice, research, memory, memory panel, and safe mode controls.
- Kept the single-chat OpenWebUI flow intact while routing chat requests through `mws/router` and using `metadata.manual_override` for manual model selection.
- Added assistant-side transparency chips for effective mode, resolved model, inferred/returned tool path, memory result, and live streaming state.
- Added a dedicated in-chat memory panel that lists remembered facts, supports per-item deletion, and allows full memory clearing.
- Preserved existing markdown/code/table/citation/image/file rendering while improving chat-level transparency around the response lifecycle.
- Added Cypress smoke coverage for the new unified chat controls and memory panel toggle.

### Contract Check

- Reused the existing request contract from `docs/CONTRACTS.md` without introducing new backend fields.
- Frontend now actively uses the documented `metadata.manual_override` and `metadata.memory` fields.

### Final pass in `feat/chat-panel-manual-mode`

- Verified the new UI remains layered on top of the base OpenWebUI chat rendering path instead of replacing it with separate screens.
- Markdown rendering remains covered by `src/lib/components/chat/Messages/Markdown.svelte` and `MarkdownTokens.svelte`.
- Code blocks and copy-code remain covered by `src/lib/components/chat/Messages/CodeBlock.svelte` via the existing `copyCode()` control.
- Table rendering remains covered by the existing `MarkdownTokens.svelte` table branch and CSV export affordance.
- Image preview remains covered by existing `Image` usage in composer attachments and assistant message files.
- File chips remain covered by existing `FileItem` usage in composer attachments and assistant message files.
- Citations/source rendering remains covered by `src/lib/components/chat/Messages/Citations.svelte`, mounted from `ResponseMessage.svelte` for `sources` and `citations`.
- Improved assistant progress transparency: pending responses now show `Routing...`, `Streaming`, and `Memory pending` states until router/tool/memory metadata resolves.
- Memory transparency now distinguishes `Memory disabled`, `Memory pending`, `Memory saved`, and `Memory unchanged`.

### Demo Artifacts

- `demo-assets/ui/01-unified-chat-controls.svg`: unified composer controls preview.
- `demo-assets/ui/02-assistant-transparency.svg`: assistant model/tool/memory/streaming chips preview.
- `demo-assets/ui/03-memory-panel.svg`: in-chat memory panel preview.
- `demo-assets/ui/04-rendering-coverage.svg`: rendering coverage preview for markdown, tables, code, files, images, and citations.
- These are static presentation preview captures because this workstation has no installed frontend dependencies; refresh with runtime screenshots after `node_modules` is restored.

### Verification Notes

- `git diff --check`: passed.
- Local code sanity check confirmed existing OpenWebUI render components still own markdown, code blocks, copy code, tables, image previews, file chips, and citations.
- `npm run check`: not run successfully because `node_modules` is absent and `svelte-kit` is unavailable.
- `npm run build`: not run successfully because `node_modules` is absent and `pyodide` cannot be resolved from `scripts/prepare-pyodide.js`.

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
