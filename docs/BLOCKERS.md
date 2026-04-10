# 2026-04-10

- Local environment is missing `pytest`, so the new router tests were added but could not be executed through pytest.
- Import-time backend smoke tests that load the full `open_webui` package are blocked by missing local Python dependencies such as `typer`.
- Automatic memory extraction from completed assistant responses is not implemented yet; the current backend supports typed fact/summary records, retrieval before answer, preferences, and forget/delete semantics.
