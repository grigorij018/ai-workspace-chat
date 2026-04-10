# Blockers and Risks

## Active Blockers

- Continuous PR watching and post-merge smoke execution cannot be automated from this branch alone; that requires team process or additional GitHub automation around `develop`.
- Real end-to-end chat verification is blocked on valid MWS GPT credentials and agreed demo model IDs.
- Local environment is missing `pytest`, so the new router tests were added but could not be executed through pytest.
- Import-time backend smoke tests that load the full `open_webui` package are blocked by missing local Python dependencies such as `typer`.
- Automatic memory extraction from completed assistant responses is not implemented yet; the current backend supports typed fact/summary records, retrieval before answer, preferences, and forget/delete semantics.

## Risks

- If `DEFAULT_MODELS` is left empty, the demo may rely on manual provider/model setup inside the UI.
- The current local happy path uses SQLite for simplicity; concurrent team usage may later need Postgres or another shared database profile.
- Existing Cypress coverage is sensitive to UI copy and selectors, so frontend smoke should stay intentionally small.
- The optional Ollama sidecar still starts with the default compose stack; this is acceptable for compatibility but not required for the MWS-only demo path.

## Mitigations

- Keep the demo checklist explicit and rehearse with a real `.env` before the handoff.
- Use repository or organization secrets for CI, never committed values.
- Expand smoke tests only after the model IDs and auth/bootstrap policy are stable.
- Install backend Python dependencies in the shared dev environment before running full router/backend test passes.
- Treat automatic memory extraction as a follow-up implementation item, while keeping manual/typed memory records available for the demo path.