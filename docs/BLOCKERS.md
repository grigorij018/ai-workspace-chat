# Blockers and Risks

## Active Blockers

- Continuous PR watching and post-merge smoke execution cannot be automated from this branch alone; that requires team process or additional GitHub automation around `develop`.
- Real end-to-end chat verification is blocked on valid MWS GPT credentials and agreed demo model IDs.

## Risks

- If `DEFAULT_MODELS` is left empty, the demo may rely on manual provider/model setup inside the UI.
- The current local happy path uses SQLite for simplicity; concurrent team usage may later need Postgres or another shared database profile.
- Existing Cypress coverage is sensitive to UI copy and selectors, so frontend smoke should stay intentionally small.
- The optional Ollama sidecar still starts with the default compose stack; this is acceptable for compatibility but not required for the MWS-only demo path.

## Mitigations

- Keep the demo checklist explicit and rehearse with a real `.env` before the handoff.
- Use repository or organization secrets for CI, never committed values.
- Expand smoke tests only after the model IDs and auth/bootstrap policy are stable.
