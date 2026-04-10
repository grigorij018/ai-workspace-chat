# Blockers and Risks

## Active Blockers

- Continuous PR watching and post-merge smoke execution cannot be automated from this branch alone; that requires team process or additional GitHub automation around `develop`.
- Real end-to-end chat verification is blocked on valid MWS GPT credentials and agreed demo model IDs.
- Real multimodal capability matrix verification is currently blocked because `https://api.gpt.mws.ru/v1/models` returns `401` without a valid MWS API key in `.env`.
- Real ASR/Whisper verification against MWS is blocked by the same missing credential; `https://api.gpt.mws.ru/v1/audio/transcriptions` currently returns `401`.
- Real image-generation verification against MWS is blocked by the same missing credential; `https://api.gpt.mws.ru/v1/images/generations` currently returns `401`.
- Real RAG embedding verification against MWS is blocked until `.env` provides `RAG_OPENAI_API_KEY`/`MWS_API_KEY` and an agreed `RAG_EMBEDDING_MODEL`.
- Real web/deep-research verification depends on a working web-search provider configuration and outbound access from the demo environment.
- Local environment is missing `pytest`, so the new router tests were added but could not be executed through pytest.
- Import-time backend smoke tests that load the full `open_webui` package are blocked by missing local Python dependencies such as `typer`.
- Frontend type/svelte checks are blocked in this workspace because the local JS toolchain dependencies are not installed (`svelte-kit: command not found`).
- Automatic memory extraction from completed assistant responses is not implemented yet; the current backend supports typed fact/summary records, retrieval before answer, preferences, and forget/delete semantics.
- The frontend memory transparency badge can currently detect newly created memory rows, but it cannot prove semantic extraction success when backend memory behavior only updates existing records or skips auto-save entirely.
- `git push` from this workstation may be blocked in some worktrees by SSH auth (`Permission denied (publickey)`), so completed local commits may need a working GitHub SSH key or an alternate push environment.

## Risks

- If `DEFAULT_MODELS` is left empty, the demo may rely on manual provider/model setup inside the UI.
- The current local happy path uses SQLite for simplicity; concurrent team usage may later need Postgres or another shared database profile.
- Existing Cypress coverage is sensitive to UI copy and selectors, so frontend smoke should stay intentionally small.
- The optional Ollama sidecar still starts with the default compose stack; this is acceptable for compatibility but not required for the MWS-only demo path.
- Manual model override now participates in router preprocessing for multimodal requests; this is intended, but it should be re-smoke-tested with real MWS credentials before demo.
- Full demo readiness still depends on valid `.env` values for MWS chat, ASR, vision, and image generation model IDs because local static smoke cannot validate provider-side modality support.

## Mitigations

- Keep the demo checklist explicit and rehearse with a real `.env` before the handoff.
- Use repository or organization secrets for CI, never committed values.
- Expand smoke tests only after the model IDs and auth/bootstrap policy are stable.
- Install backend Python dependencies in the shared dev environment before running full router/backend test passes.
- Install frontend dependencies before relying on `npm run check`, `npm run build`, or broader chat UI validation.
- Run `python3 scripts/smoke-multimodal-contract.py` as a dependency-light guard until full backend/frontend dependencies are available.
- Treat automatic memory extraction as a follow-up implementation item, while keeping manual/typed memory records available for the demo path.
- Validate the new auto/manual UI against a live MWS environment before demo so the displayed selected model and tool path match real router outputs in streaming mode.
