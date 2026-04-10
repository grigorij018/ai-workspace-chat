import re
from pathlib import Path
from typing import Optional

from fastapi import HTTPException

from open_webui.models.files import Files
from open_webui.orchestrator.registry import build_router_model
from open_webui.orchestrator.schemas import RouterDecision
from open_webui.storage.provider import Storage


ROUTER_MODEL_ID = 'mws/router'

IMAGE_PROMPT_PATTERN = re.compile(r'(нарисуй|сгенерируй|создай изображение|draw|generate image|create image)', re.I)
WEB_SEARCH_PATTERN = re.compile(r'(search|research|latest|news|найди|поиск|исследуй|последн|актуальн)', re.I)
URL_PATTERN = re.compile(r'https?://[^\s)]+', re.I)


def _extract_prompt(messages: list[dict]) -> str:
    for message in reversed(messages):
        if message.get('role') != 'user':
            continue
        content = message.get('content', '')
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts = [part.get('text', '') for part in content if part.get('type') == 'text']
            return '\n'.join(text_parts).strip()
    return ''


def _detect_message_images(messages: list[dict]) -> bool:
    for message in messages:
        content = message.get('content')
        if isinstance(content, list) and any(part.get('type') == 'image_url' for part in content):
            return True
    return False


def _resolve_file_content_type(file_item: dict) -> str:
    return (
        file_item.get('content_type')
        or file_item.get('meta', {}).get('content_type')
        or ''
    ).lower()


def _get_attachment_key(file_item: dict) -> str:
    return str(file_item.get('id') or file_item.get('url') or file_item.get('name') or file_item)


def _infer_attachment_hint(file_item: dict) -> dict:
    file_type = (file_item.get('type') or '').lower()
    content_type = _resolve_file_content_type(file_item)
    modality = 'file'
    routing_intent = 'file'
    transcription_requested = False

    if file_type == 'url':
        modality = 'url'
        routing_intent = 'url'
    elif file_type == 'image' or content_type.startswith('image/'):
        modality = 'image'
        routing_intent = 'vision'
    elif file_type == 'audio' or content_type.startswith(('audio/', 'video/')):
        modality = 'audio'
        routing_intent = 'audio'
        transcription_requested = True
    elif content_type in ('text/uri-list',):
        modality = 'url'
        routing_intent = 'url'

    return {
        'key': _get_attachment_key(file_item),
        'id': file_item.get('id'),
        'name': file_item.get('name'),
        'content_type': content_type,
        'modality': modality,
        'routing_intent': routing_intent,
        'transcription_requested': transcription_requested,
    }


def _build_attachment_hints(files: list[dict], metadata: Optional[dict] = None) -> list[dict]:
    hints_by_key = {}

    for hint in (metadata or {}).get('attachment_hints') or []:
        key = str(hint.get('key') or hint.get('id') or hint.get('name') or hint.get('content_type') or len(hints_by_key))
        hints_by_key[key] = {**hint, 'key': key}

    for file_item in files:
        inferred = _infer_attachment_hint(file_item)
        key = inferred['key']
        hints_by_key[key] = {
            **inferred,
            **hints_by_key.get(key, {}),
            **{k: v for k, v in inferred.items() if v not in (None, '', False)},
            'key': key,
        }

    return list(hints_by_key.values())


def _classify_task(prompt: str, files: list[dict], messages: list[dict], attachment_hints: list[dict]) -> str:
    has_image = _detect_message_images(messages) or any(
        hint.get('modality') == 'image' for hint in attachment_hints
    )
    has_audio = any(hint.get('modality') == 'audio' for hint in attachment_hints)
    has_url_file = any(hint.get('modality') == 'url' for hint in attachment_hints)
    has_file = any(hint.get('modality') == 'file' for hint in attachment_hints)

    for file_item in files:
        file_type = (file_item.get('type') or '').lower()
        content_type = _resolve_file_content_type(file_item)
        if file_type == 'url':
            has_url_file = True
        elif file_type == 'image' or content_type.startswith('image/'):
            has_image = True
        elif file_type == 'audio' or content_type.startswith('audio/'):
            has_audio = True
        else:
            has_file = True

    if has_audio:
        return 'audio'
    if IMAGE_PROMPT_PATTERN.search(prompt or ''):
        return 'image_generation'
    if has_image and (prompt or '').strip():
        return 'vision'
    if has_file:
        return 'file'
    if has_url_file or URL_PATTERN.search(prompt or ''):
        return 'url'
    if WEB_SEARCH_PATTERN.search(prompt or ''):
        return 'web_research'
    return 'text'


def _get_model_capabilities(model: dict) -> dict:
    return ((model.get('info') or {}).get('meta') or {}).get('capabilities') or {}


def _select_model(
    models: dict[str, dict],
    task_type: str,
    manual_override: Optional[str] = None,
    allow_fallback: bool = True,
) -> Optional[str]:
    if manual_override and manual_override in models:
        return manual_override

    priorities = {
        'text': lambda caps: caps.get('text') and not caps.get('embeddings') and not caps.get('image_generation'),
        'vision': lambda caps: caps.get('vision'),
        'audio': lambda caps: caps.get('text') and not caps.get('embeddings'),
        'image_generation': lambda caps: caps.get('image_generation'),
        'file': lambda caps: caps.get('text'),
        'url': lambda caps: caps.get('text'),
        'web_research': lambda caps: caps.get('text'),
    }

    predicate = priorities[task_type]
    for model_id, model in models.items():
        if model_id == ROUTER_MODEL_ID:
            continue
        if predicate(_get_model_capabilities(model)):
            return model_id

    if allow_fallback:
        for model_id in models:
            if model_id != ROUTER_MODEL_ID:
                return model_id
        return ROUTER_MODEL_ID
    return None


def build_router_model_entry() -> dict:
    return build_router_model(ROUTER_MODEL_ID)


def _build_reason(task_type: str, manual_override: bool) -> str:
    if manual_override:
        return 'User selected a manual model override.'

    reasons = {
        'text': 'Defaulted to text generation.',
        'audio': 'Detected audio input and enabled ASR preprocessing.',
        'vision': 'Image attachment with a question was detected.',
        'image_generation': 'Detected image-generation intent from the prompt.',
        'file': 'Detected attached file content and enabled file QA retrieval.',
        'url': 'Detected URL content and enabled URL parsing pipeline.',
        'web_research': 'Detected latest/search intent and enabled web research pipeline.',
    }
    return reasons[task_type]


def apply_router_decision(
    request,
    form_data: dict,
    metadata: dict,
    decision: RouterDecision,
    attachment_hints: Optional[list[dict]] = None,
):
    features = form_data.get('features') or {}
    files = form_data.get('files') or []
    prompt = _extract_prompt(form_data.get('messages', []))

    form_data['model'] = decision.selected_model

    if decision.task_type == 'web_research':
        features['web_search'] = True
    elif decision.task_type == 'image_generation':
        features['image_generation'] = True
    elif decision.task_type == 'url':
        urls = URL_PATTERN.findall(prompt)
        for url in urls:
            files.append({'name': url, 'url': url, 'type': 'url'})

    form_data['features'] = features
    if files:
        form_data['files'] = list({str(item): item for item in files}.values())

    metadata['router_decision'] = decision.model_dump()
    metadata['selected_model_id'] = decision.selected_model
    metadata['manual_override'] = decision.manual_override
    metadata['attachment_hints'] = attachment_hints or metadata.get('attachment_hints') or []
    return form_data, metadata


def _get_audio_file_path(file_item: dict) -> Optional[str]:
    file_id = file_item.get('id')
    if not file_id:
        return None

    file_model = Files.get_file_by_id(file_id)
    if not file_model or not file_model.path:
        return None

    path = Path(Storage.get_file(file_model.path))
    return str(path) if path.is_file() else None


def maybe_transcribe_audio(request, form_data: dict, user) -> dict:
    files = form_data.get('files') or []
    audio_file = next(
        (
            file_item
            for file_item in files
            if (file_item.get('type') == 'audio') or _resolve_file_content_type(file_item).startswith('audio/')
        ),
        None,
    )
    if not audio_file:
        return form_data

    file_path = _get_audio_file_path(audio_file)
    if not file_path:
        raise HTTPException(status_code=400, detail='Audio attachment could not be prepared for transcription.')

    from open_webui.routers.audio import transcribe

    try:
        result = transcribe(request, file_path, user=user)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f'Audio transcription is unavailable: {exc}') from exc

    transcript = (result or {}).get('text', '').strip()
    if not transcript:
        raise HTTPException(status_code=400, detail='Audio transcription returned empty text.')

    messages = form_data.get('messages', [])
    for message in reversed(messages):
        if message.get('role') == 'user':
            content = message.get('content', '')
            prefix = f'[Audio transcript]\n{transcript}'
            if isinstance(content, str):
                message['content'] = prefix if not content else f'{prefix}\n\n{content}'
            elif isinstance(content, list):
                message['content'] = [{'type': 'text', 'text': prefix}, *content]
            break

    return form_data


def route_chat_request(request, form_data: dict, user, metadata: dict, model: dict):
    manual_override = metadata.get('manual_override')
    should_route = model.get('id') == ROUTER_MODEL_ID or bool(manual_override)
    if not should_route:
        return form_data, metadata, model, None

    models = request.app.state.MODELS or {}
    if manual_override and manual_override not in models:
        raise HTTPException(status_code=404, detail=f'Manual model override {manual_override} is unavailable.')

    prompt = _extract_prompt(form_data.get('messages', []))
    files = form_data.get('files') or metadata.get('files') or []
    attachment_hints = _build_attachment_hints(files, metadata)
    task_type = _classify_task(prompt, files, form_data.get('messages', []), attachment_hints)
    selected_model = _select_model(
        models,
        task_type,
        manual_override=manual_override,
        allow_fallback=task_type in {'text', 'audio', 'file', 'url', 'web_research', 'image_generation'},
    )
    if not selected_model:
        raise HTTPException(status_code=400, detail=f'No model is available for task type {task_type}.')

    tool_map = {
        'text': 'text_llm',
        'audio': 'asr',
        'vision': 'vlm',
        'image_generation': 'image_generation',
        'file': 'file_qa',
        'url': 'url_parse',
        'web_research': 'web_research',
    }
    confidence_map = {
        'text': 0.72,
        'audio': 0.93,
        'vision': 0.9,
        'image_generation': 0.95,
        'file': 0.9,
        'url': 0.88,
        'web_research': 0.94,
    }

    decision = RouterDecision(
        task_type=task_type,
        selected_model=selected_model,
        selected_tool=tool_map[task_type],
        manual_override=bool(manual_override),
        confidence=1.0 if manual_override else confidence_map[task_type],
        short_reason=_build_reason(task_type, bool(manual_override)),
    )

    if task_type == 'vision':
        selected_caps = _get_model_capabilities(models.get(selected_model, {}))
        if not selected_caps.get('vision'):
            detail = (
                f'Model {selected_model} does not support image understanding.'
                if manual_override
                else 'No vision-capable model is currently available for image understanding.'
            )
            raise HTTPException(status_code=400, detail=detail)

    form_data, metadata = apply_router_decision(
        request,
        form_data,
        metadata,
        decision,
        attachment_hints=attachment_hints,
    )
    if task_type == 'audio':
        form_data = maybe_transcribe_audio(request, form_data, user)
        if not manual_override:
            text_model = _select_model(models, 'text', allow_fallback=False)
            if not text_model:
                raise HTTPException(status_code=400, detail='No text model is available for the post-ASR chat step.')
            decision.selected_model = text_model
            metadata['router_decision'] = decision.model_dump()
            metadata['selected_model_id'] = text_model
            form_data['model'] = text_model

    routed_model = models.get(form_data['model'], model)
    return form_data, metadata, routed_model, decision
