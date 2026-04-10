# Feature Matrix

| Area | Requirement | Current release baseline | Notes |
| --- | --- | --- | --- |
| Unified chat UX | One primary chat surface | Ready | Smoke covers landing in the main chat flow |
| One-command start | Teammate can boot locally without manual steps | Ready | `make up` + `make smoke` |
| Model gateway | All model traffic through MWS GPT | Configured | Requires `OPENAI_API_KEY` in `.env` or CI secrets |
| Manual model selection | User can still choose models | Configured | Backed by `DEFAULT_MODELS` and Open WebUI model picker |
| Auto-routing | Manual and auto modes can coexist | Deferred to feature teams | Infra leaves `TASK_MODEL` / `TASK_MODEL_EXTERNAL` hooks in place |
| Memory | Transparent and user-manageable | Not changed in this stage | No business-logic edits in this branch |
| File workflows | Operate from chat | Inherited from Open WebUI | Not reworked here |
| Web/research workflows | Operate from chat | Inherited from Open WebUI | Optional Playwright sidecar remains available |
| Auth bootstrap | First teammate can create admin and log in | Ready | Covered by shell smoke and Cypress smoke |
| Persistence | Session/data survive restarts | Ready | Docker volume-backed SQLite |
| Docker docs | Clear prerequisites/setup/run/env instructions | Ready | README + docs updated |
| CI lint | Prevent drift and broken config | Ready | GitHub Actions workflow added |
| Backend tests | Minimal reliable pytest coverage | Ready | Targeted smoke test job |
| Frontend smoke | Detect broken chat landing/auth flow | Ready | Cypress smoke against running stack |
| Release/demo pack | Team can rehearse demo consistently | Ready | Demo checklist added |
| API contracts | No undocumented shared API change | Ready | No contract change in this stage |
