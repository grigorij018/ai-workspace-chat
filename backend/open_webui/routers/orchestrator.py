import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from open_webui.orchestrator.client import get_mws_client
from open_webui.orchestrator.registry import apply_capabilities
from open_webui.orchestrator.router import build_router_model_entry, route_chat_request
from open_webui.orchestrator.schemas import ChatRequest, RouterDecision
from open_webui.utils.auth import get_admin_user, get_verified_user

log = logging.getLogger(__name__)

router = APIRouter()


@router.post('/models/sync')
async def sync_models(request: Request, user=Depends(get_admin_user)):
    client = get_mws_client()
    try:
        response = await client.models.list()
    except Exception as exc:
        log.exception(exc)
        raise HTTPException(status_code=502, detail='Failed to sync models from MWS')

    items = []
    for model in response.data:
        items.append(
            apply_capabilities(
                {
                    'id': model.id,
                    'name': getattr(model, 'name', None) or model.id,
                    'object': 'model',
                    'owned_by': 'openai',
                    'connection_type': 'external',
                    'created': 0,
                    'info': {'meta': {}},
                }
            )
        )

    router_model = build_router_model_entry()
    synced_models = [router_model, *items]
    request.app.state.OPENAI_MODELS = {model['id']: model for model in items}
    return {'data': synced_models}


@router.post('/decision', response_model=RouterDecision)
async def preview_router_decision(request: Request, form_data: ChatRequest, user=Depends(get_verified_user)):
    metadata = dict(form_data.metadata)
    working_form_data = form_data.model_dump()
    working_form_data['files'] = form_data.files
    model = request.app.state.MODELS.get(form_data.model)
    if not model:
        raise HTTPException(status_code=404, detail='Model not found')

    _, _, _, decision = route_chat_request(request, working_form_data, user, metadata, model)
    if not decision:
        raise HTTPException(status_code=400, detail='Routing is available only for router/manual-override requests')
    return decision
