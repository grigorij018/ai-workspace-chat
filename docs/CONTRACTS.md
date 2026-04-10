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
    "image_generation": false
  },
  "metadata": {
    "chat_id": "chat_123",
    "message_id": "msg_123",
    "manual_override": null,
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
- `task_type`: `text`, `audio`, `vision`, `image_generation`, `file`, `url`, `web_research`
- `selected_model`: concrete MWS-backed model used for the answering step
- `selected_tool`: `text_llm`, `asr`, `vlm`, `image_generation`, `file_qa`, `url_parse`, `web_research`
- `manual_override`: true when the user explicitly forced a model
- `confidence`: float in `[0, 1]`
- `short_reason`: short human-readable explanation suitable for chat metadata/debugging
