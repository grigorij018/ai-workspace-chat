# Backend Contracts

## ChatRequest

```json
{
  "model": "mws/router",
  "messages": [
    {
      "role": "user",
      "content": "Найди последние новости по теме"
    }
  ],
  "files": [],
  "features": {
    "memory": true,
    "web_search": false,
    "deep_research": false,
    "pptx_generation": false,
    "image_generation": false
  },
  "metadata": {
    "chat_id": "chat_123",
    "message_id": "msg_123",
    "manual_override": null,
    "attachment_hints": [
      {
        "name": "voice-note.webm",
        "content_type": "audio/webm",
        "modality": "audio",
        "routing_intent": "audio",
        "transcription_requested": true
      }
    ],
    "memory": {
      "enabled": true,
      "save": true
    }
  }
}
```

Notes:
- `model` may point to a concrete MWS-backed model or the virtual auto-router model `mws/router`.
- `metadata.manual_override` forces a concrete model and bypasses auto-selection.
- `files` may include uploaded files, images, audio, urls, collections, and web-search artifacts.
- `metadata.attachment_hints` is optional normalized attachment metadata produced from MIME types and UI context.
- Audio uploads should prefer `content_type`/`meta.content_type` like `audio/webm`, `audio/mpeg`, or `audio/wav`.
- Image understanding stays in the same chat flow: user text plus one or more image attachments in `files`.
- Audio requests that are successfully transcribed should continue through the normal shared chat pipeline as text.
- File QA uses the existing chat `files` array and retrieval pipeline. Supported demo formats are `pdf`, `docx`, `xlsx`, `csv`, `txt`, and `md`; processing is `parse -> chunk -> embed -> retrieve -> cite`.
- URL parsing uses `files` entries with `type=url`, `url`, and `name`. Plain URLs in user text are normalized into the same shape by the router.
- Deep research uses `features.deep_research=true` and must stay in the same chat completion path. It performs multi-query web search, fetches/deduplicates sources, stores/retrieves web collections when embeddings are enabled, and instructs the answering model to return a concise structured answer with citations.
- PPTX generation uses `features.pptx_generation=true`; the backend creates a `.pptx` artifact from the current chat context and returns it as a normal assistant file attachment.

## ChatResponse

```json
{
  "id": "chatcmpl_x",
  "object": "chat.completion",
  "model": "gpt-4.1-mini",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "..."
      },
      "finish_reason": "stop"
    }
  ],
  "router_decision": {
    "task_type": "web_research",
    "selected_model": "gpt-4.1-mini",
    "selected_tool": "web_research",
    "manual_override": false,
    "confidence": 0.94,
    "short_reason": "Detected latest/search intent and enabled web research pipeline."
  }
}
```

Notes:
- `router_decision` is returned for routed chats and omitted for plain direct calls when routing is not involved.
- Streaming responses must emit the same routing metadata before normal deltas when available.

## ToolResult

```json
{
  "tool_name": "web_research",
  "status": "success",
  "content": "Short tool output",
  "files": [],
  "metadata": {
    "collection_names": [
      "web-search-abc"
    ]
  }
}
```

Notes:
- `status` is `success` or `error`.
- `files` is optional and contains any produced artifacts that should flow back into chat.

## MemoryRecord

```json
{
  "id": "mem_123",
  "user_id": "user_123",
  "kind": "fact",
  "content": "User prefers concise Russian answers.",
  "source": "chat",
  "enabled": true,
  "created_at": 1710000000,
  "updated_at": 1710000000
}
```

Notes:
- `kind` is `fact` or `summary`.
- `enabled=false` means the record is forgotten for retrieval without hard-deleting audit/history requirements.

## RouterDecision

```json
{
  "task_type": "vision",
  "selected_model": "gpt-4.1",
  "selected_tool": "vlm",
  "manual_override": false,
  "confidence": 0.91,
  "short_reason": "Image attachment with a user question was detected."
}
```

Field rules:
- `task_type`: `text`, `audio`, `vision`, `image_generation`, `file`, `url`, `web_research`, `deep_research`, `pptx_generation`
- `selected_model`: concrete MWS-backed model used for the answering step
- `selected_tool`: `text_llm`, `asr`, `vlm`, `image_generation`, `file_qa`, `url_parse`, `web_research`, `deep_research`, `pptx_generation`
- `manual_override`: true when the user explicitly forced a model
- `confidence`: float in `[0, 1]`
- `short_reason`: short human-readable explanation suitable for chat metadata/debugging

## Attachment Hint

```json
{
  "name": "photo.png",
  "content_type": "image/png",
  "modality": "image",
  "routing_intent": "vision",
  "transcription_requested": false
}
```

Field rules:
- `modality`: `audio`, `image`, `file`, `url`, or `unknown`
- `routing_intent`: normalized router hint derived from MIME/UI context; expected values are `audio`, `vision`, `file`, `url`, `image_generation`, or `text`
- `transcription_requested`: true when the client expects ASR preprocessing for this attachment

## Attachment Response Flow

Notes:
- Assistant-side image generation returns generated image files as normal chat message attachments.
- Streaming/file events should keep using the existing chat event channel and emit `chat:message:files` when generated artifacts are ready.
- Soft failures for missing modality support or missing access should surface as normal chat errors/status updates instead of forcing a separate multimodal screen.

## Multimodal Chat Paths

Audio file upload:
- Client uploads an audio/video MIME attachment through the normal chat composer.
- The attachment adapter emits `routing_intent=audio` and `transcription_requested=true`.
- Router runs ASR preprocessing, prepends the transcript as `[Audio transcript]`, switches to a text model when auto-routed, and continues through the normal chat completion path.
- Missing file access, empty transcripts, missing ASR access, or unsupported audio MIME should return normal chat errors/status updates.

Microphone input:
- The existing `VoiceRecording` chat component records browser audio with `MediaRecorder`.
- It calls the `/audio/transcriptions` frontend API helper and inserts returned text into the existing composer.
- The user can then send that text through the same chat request pipeline as typed text.

Image understanding:
- Client sends the image attachment as an `image_url` content part plus an attachment hint with `routing_intent=vision`.
- Router selects a vision-capable model when available.
- If a manually selected model lacks vision capability, the request should fail gracefully with a chat-visible error instead of attempting a non-vision call.

Image generation:
- Text prompts matching generation intent set `features.image_generation=true`.
- The backend image generation handler emits generated artifacts through the existing chat file event path.
- Assistant messages render those generated images as normal message attachments with `id`, `name`, `content_type`, and `url` when available.

File, URL, Research, PPTX:
- Uploaded `pdf`, `docx`, `xlsx`, `csv`, `txt`, and `md` files are processed through the retrieval pipeline and queried from the same chat turn when attached.
- URL turns attach normalized URL file entries and retrieve fetched page text as a source, enabling summarization and Q&A with citations.
- Web search turns set `features.web_search=true`; deep research turns set both `features.web_search=true` and `features.deep_research=true`.
- PPTX turns create a chat-visible `.pptx` file artifact and then let the normal assistant response acknowledge it.
