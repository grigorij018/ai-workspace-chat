# Status

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

### Contract Check

- No shared API changes in this stage.
- [docs/CONTRACTS.md](CONTRACTS.md) does not need an update for these infra/docs-only changes.

### Verification Notes

- `bash ./scripts/check-no-secrets.sh`: passed
- `docker compose --env-file .env config`: passed with a temporary local `.env`
- Local `make up` could not complete in this workstation session because the Docker daemon was not available

### Next Useful Steps

- Validate the exact MWS model IDs the demo should pin in `DEFAULT_MODELS` and `TASK_MODEL`.
- Extend smoke coverage from auth/landing into one real chat completion in an environment with demo credentials.
- Decide whether SQLite remains enough for demo/release or whether Postgres becomes a required profile later.
