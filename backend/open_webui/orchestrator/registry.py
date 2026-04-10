import re

from open_webui.config import MWS_ROUTER_MODEL_NAME


def infer_capabilities(model: dict) -> dict[str, bool]:
    info = model.get('info', {}) or {}
    meta = info.get('meta', {}) or {}
    existing = meta.get('capabilities') or {}

    model_id = (model.get('id') or '').lower()
    model_name = (model.get('name') or '').lower()
    haystack = f'{model_id} {model_name}'

    capabilities = {
        'text': True,
        'vision': bool(
            existing.get('vision')
            or re.search(r'(vision|vlm|omni|4o|gpt-4\.1|gemini|claude-3|claude-4)', haystack)
        ),
        'audio': bool(
            existing.get('audio')
            or re.search(r'(audio|asr|stt|transcribe|whisper|voxtral)', haystack)
        ),
        'embeddings': bool(
            existing.get('embeddings')
            or re.search(r'(embedding|embed|text-embedding)', haystack)
        ),
        'image_generation': bool(
            existing.get('image_generation')
            or re.search(r'(gpt-image|dall-e|imagen|image-gen|image generation)', haystack)
        ),
        'memory': bool(existing.get('memory', True)),
        'file_context': bool(existing.get('file_context', True)),
        'web_search': bool(existing.get('web_search', True)),
        'builtin_tools': bool(existing.get('builtin_tools', True)),
    }

    if capabilities['embeddings']:
        capabilities['text'] = False

    if capabilities['image_generation'] or capabilities['audio']:
        capabilities['text'] = capabilities['text'] and not re.search(r'(tts-1|whisper|transcribe)', haystack)

    return capabilities


def apply_capabilities(model: dict) -> dict:
    model = {**model}
    info = {**(model.get('info') or {})}
    meta = {**(info.get('meta') or {})}
    meta['capabilities'] = {
        **infer_capabilities(model),
        **(meta.get('capabilities') or {}),
    }
    info['meta'] = meta
    model['info'] = info
    return model


def build_router_model(router_model_id: str) -> dict:
    return {
        'id': router_model_id,
        'name': MWS_ROUTER_MODEL_NAME,
        'object': 'model',
        'created': 0,
        'owned_by': 'openai',
        'connection_type': 'external',
        'preset': True,
        'info': {
            'meta': {
                'description': 'Virtual auto-router model backed by MWS GPT.',
                'capabilities': {
                    'text': True,
                    'vision': True,
                    'audio': True,
                    'embeddings': True,
                    'image_generation': True,
                    'memory': True,
                    'web_search': True,
                    'builtin_tools': True,
                    'file_context': True,
                },
            }
        },
        'tags': [{'name': 'router'}, {'name': 'mws'}],
    }
