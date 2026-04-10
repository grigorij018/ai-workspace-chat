# Research and File Workflows Runbook

This runbook covers the `feat/research-file-workflows` demo path. All flows stay inside the existing OpenWebUI chat UX and reuse the current message, source, citation, and file attachment rendering paths.

## End-to-End Flows

### File QA

Path:
`chat file attachment -> process_file -> Loader -> Document[] -> chunking -> embeddings -> vector DB -> get_sources_from_items -> answer with sources`

Expected behavior:
- The user attaches a supported file and asks a question in chat.
- Upload processing extracts text with the existing retrieval loader stack.
- `save_docs_to_vector_db` splits the extracted documents using the configured text splitter, generates embeddings through the configured RAG embedding function, and writes chunks to the file collection.
- During the chat turn, `chat_completion_files_handler` queries the attached file collection, injects retrieved context into the normal model messages, and emits sources for the existing citation UI.
- The assistant answers in the same chat thread with source/citation metadata attached to the response.

### URL Summary and Q&A

Path:
`user message URL -> router type=url -> files[{ type=url }] -> get_content_from_url -> retrieval source -> summary/Q&A answer`

Expected behavior:
- A plain URL in the user message is normalized into a `type=url` file entry by the router.
- The retrieval source path fetches and parses the URL content through the existing web loader.
- The assistant can summarize the page or answer follow-up questions against the fetched page text.
- Citations render through the same source event path as other retrieval-backed answers.

### Deep Research

Path:
`research prompt -> router type=deep_research -> features.web_search + features.deep_research -> generate_queries -> process_web_search -> deduped URLs -> retrieved web collection -> concise cited answer`

Expected behavior:
- Prompts such as `Deep research: compare RAG approaches` select `selected_tool=deep_research`.
- The search handler performs multi-query expansion, includes the original user request, fetches top sources, deduplicates URLs, and attaches either a web-search collection or fetched docs to the chat files.
- The answer contract asks the model for a concise structured response with key findings, caveats, and sources.
- Sources/citations are emitted through the existing chat source metadata, so this does not replace or fork `ResponseMessage` rendering.

### PPTX Export

Path:
`chat prompt -> router type=pptx_generation -> chat_pptx_generation_handler -> create_chat_pptx_file -> event type=files -> assistant attachment`

Example prompt:
`Собери презентацию по текущему диалогу`

Expected artifact:
- File name pattern: `ai-workspace-research-<unix_timestamp>.pptx`
- Content type: `application/vnd.openxmlformats-officedocument.presentationml.presentation`
- Delivery: existing chat file attachment event with a `/api/v1/files/<id>/content?attachment=true` download URL.

Minimum slide structure:
- `AI Workspace`
- `Problem`
- `Solution`
- `Architecture`
- `Demo Flow`
- `Value`
- `Roadmap`

## Acceptance Matrix

| Input | Expected ingestion | Expected chat result | Local verification |
| --- | --- | --- | --- |
| `pdf` | `PyPDFLoader` extracts pages, splitter chunks content, embedding function stores `file-<id>` vectors. | User asks about the PDF; assistant answers with file sources. | Loader and file workflow contract checked by `scripts/smoke-research-file-workflows.py`; live embedding blocked without `.env`. |
| `docx` | `Docx2txtLoader` extracts document text before chunking and embedding. | User asks about the document; assistant answers from retrieved chunks. | Loader and file workflow contract checked by smoke; live embedding blocked without `.env`. |
| `xlsx` | `UnstructuredExcelLoader` is preferred; `ExcelLoader`/pandas fallback extracts sheet text. | User asks about spreadsheet rows/sheets; assistant answers from retrieved sheet text. | Loader and file workflow contract checked by smoke; live embedding blocked without `.env`. |
| `csv` | `CSVLoader` extracts rows before chunking and embedding. | User asks about CSV values; assistant answers from retrieved row text. | Loader and file workflow contract checked by smoke; live embedding blocked without `.env`. |
| `txt` | `TextLoader` treats the file as plain text before chunking and embedding. | User asks about the text file; assistant answers from retrieved chunks. | `txt` is included in source/text extension coverage and smoke. |
| `md` | `TextLoader` reads markdown; markdown header splitter may preserve headings when enabled. | User asks about sections; assistant answers from retrieved markdown chunks. | `md` loader path and contract checked by smoke. |

## Cited Answer Contract

The deep research answer contract is a prompt-level constraint, not a new response schema. The model should return user-facing markdown with these sections when appropriate:
- `Summary`
- `Key findings`
- `Caveats`
- `Sources`

Citations and source rendering:
- Backend retrieval returns `sources` events using the existing source shape: `source`, `document`, `metadata`, and optional `distances`.
- Existing chat rendering keeps owning citation/source display; this branch does not introduce a new `ResponseMessage` shape.
- Web and file sources should include `source`/`name` metadata when available so the current citation renderer can label them.
- If live search or embeddings are unavailable, the assistant should surface a normal chat-visible error/status rather than sending the user to a separate screen.

## Local vs Live Verification

Checked locally:
- Router contract for `file`, `url`, `web_research`, `deep_research`, and `pptx_generation`.
- Loader coverage for `pdf`, `docx`, `xlsx`, `csv`, `txt`, and `md`.
- Deep research wiring from features to search files and answer contract.
- PPTX generation wiring to chat file attachment events.
- Python syntax for changed backend files.
- Secret discipline for `.env.example`.

Blocked on credentials/provider settings:
- Real MWS embedding calls need `RAG_OPENAI_API_KEY` or `MWS_API_KEY` plus an agreed `RAG_EMBEDDING_MODEL`.
- Real web/deep-research needs `ENABLE_WEB_SEARCH=true`, a working `WEB_SEARCH_ENGINE`, and any provider-specific credentials when the provider requires them.
- Real end-to-end answer quality and citation rendering should be rehearsed with a populated `.env` and a running app.
