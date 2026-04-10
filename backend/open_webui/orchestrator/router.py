import re
from pathlib import Path
from typing import Optional

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


def _classify_task(prompt: str, files: list[dict], messages: list[dict]) -> str:
    has_image = _detect_message_images(messages)
    has_audio = False
    has_file = False
    has_url_file = False

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


def _select_model(models: dict[str, dict], task_type: str, manual_override: Optional[str] = None) -> str:
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

    for model_id in models:
        if model_id != ROUTER_MODEL_ID:
            return model_id
    return ROUTER_MODEL_ID


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
        return form_data

    from open_webui.routers.audio import transcribe

    result = transcribe(request, file_path, user=user)
    transcript = (result or {}).get('text', '').strip()
    if not transcript:
        return form_data

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
    prompt = _extract_prompt(form_data.get('messages', []))
    files = form_data.get('files') or metadata.get('files') or []
    task_type = _classify_task(prompt, files, form_data.get('messages', []))
    selected_model = _select_model(models, task_type, manual_override=manual_override)

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

    form_data, metadata = apply_router_decision(request, form_data, metadata, decision)
    if task_type == 'audio':
        form_data = maybe_transcribe_audio(request, form_data, user)
        if not manual_override:
            text_model = _select_model(models, 'text')
            decision.selected_model = text_model
            metadata['router_decision'] = decision.model_dump()
            metadata['selected_model_id'] = text_model
            form_data['model'] = text_model

    routed_model = models.get(form_data['model'], model)
    return form_data, metadata, routed_model, decision
