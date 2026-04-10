# Demo Checklist

## Before Demo

- `.env` exists locally and is not tracked by git.
- `OPENAI_API_KEY` is set to a working MWS GPT credential.
- `WEBUI_SECRET_KEY` is non-empty.
- `make up` completes successfully.
- `make smoke` passes.
- The app opens on `http://localhost:3000`.

## Demo Script

1. Sign in or create the first admin user.
2. Confirm the landing page is the main chat workspace.
3. Open the model picker and show that manual model selection is available.
4. Mention that the configured backend path is MWS GPT through an OpenAI-compatible endpoint.
5. Send a short prompt from the main chat input.
6. Refresh the page and confirm the session/chat still exists.
7. If needed, mention optional sidecars such as Playwright/Ollama without leaving the unified chat UX.

## After Demo

- Save logs if any failure happened during rehearsal or demo.
- Record follow-up gaps in [docs/BLOCKERS.md](BLOCKERS.md).
- Update [docs/STATUS.md](STATUS.md) with demo findings.
