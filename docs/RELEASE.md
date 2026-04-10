# Release Runbook

## Scope

This branch prepares the repo for a hackathon release handoff where any teammate can start the stack locally and walk the demo path without hidden setup steps.

## Build and Verify

1. Copy `.env.example` to `.env`.
2. Fill in `OPENAI_API_KEY` and `WEBUI_SECRET_KEY`.
3. Run `make up`.
4. Run `make smoke`.
5. Open the app and walk the steps in [DEMO_CHECKLIST.md](DEMO_CHECKLIST.md).

## Release Artifacts

- Root README with setup/run/env/demo instructions
- Docker Compose baseline with `.env` support
- Make targets for startup and smoke verification
- GitHub Actions workflow for lint, backend smoke, and frontend smoke
- Docs for architecture, feature matrix, blockers, status, and demo flow

## Handoff Notes

- This stage does not modify shared API contracts.
- This stage does not rewrite business logic in agent/chat flows.
- MWS model IDs still need a final team decision before the polished demo preset is frozen.
