from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
import logging
import asyncio
from typing import Optional

from open_webui.models.memories import Memories, MemoryModel
from open_webui.orchestrator.memory import get_memory_preference, update_memory_preference
from open_webui.orchestrator.schemas import MemoryPreference
from open_webui.retrieval.vector.factory import VECTOR_DB_CLIENT
from open_webui.utils.auth import get_verified_user
from open_webui.internal.db import get_session
from sqlalchemy.orm import Session

from open_webui.utils.access_control import has_permission
from open_webui.constants import ERROR_MESSAGES

log = logging.getLogger(__name__)

router = APIRouter()


############################
# GetMemories
# Let what is remembered here spare someone the cost
# of learning it twice.
############################


@router.get('/', response_model=list[MemoryModel])
async def get_memories(
    request: Request,
    user=Depends(get_verified_user),
    db: Session = Depends(get_session),
):
    if not request.app.state.config.ENABLE_MEMORIES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    if not has_permission(user.id, 'features.memories', request.app.state.config.USER_PERMISSIONS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    return Memories.get_memories_by_user_id(user.id, db=db)


############################
# AddMemory
############################


class AddMemoryForm(BaseModel):
    content: str
    kind: str = 'fact'
    source: Optional[str] = 'chat'
    enabled: bool = True


class MemoryUpdateModel(BaseModel):
    content: Optional[str] = None
    kind: Optional[str] = None
    source: Optional[str] = None
    enabled: Optional[bool] = None


@router.post('/add', response_model=Optional[MemoryModel])
async def add_memory(
    request: Request,
    form_data: AddMemoryForm,
    user=Depends(get_verified_user),
):
    # NOTE: We intentionally do NOT use Depends(get_session) here.
    # Database operations (insert_new_memory) manage their own short-lived sessions.
    # This prevents holding a connection during EMBEDDING_FUNCTION()
    # which makes external embedding API calls (1-5+ seconds).
    if not request.app.state.config.ENABLE_MEMORIES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    if not has_permission(user.id, 'features.memories', request.app.state.config.USER_PERMISSIONS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    memory = Memories.insert_new_memory(
        user.id,
        form_data.content,
        kind=form_data.kind,
        source=form_data.source,
        enabled=form_data.enabled,
    )

    if not memory.enabled:
        return memory

    vector = await request.app.state.EMBEDDING_FUNCTION(memory.content, user=user)

    VECTOR_DB_CLIENT.upsert(
        collection_name=f'user-memory-{user.id}',
        items=[
            {
                'id': memory.id,
                'text': memory.content,
                'vector': vector,
                'metadata': {
                    'created_at': memory.created_at,
                    'kind': memory.kind,
                    'source': memory.source,
                },
            }
        ],
    )

    return memory


############################
# QueryMemory
############################


class QueryMemoryForm(BaseModel):
    content: str
    k: Optional[int] = 1
    kind: Optional[str] = None


@router.post('/query')
async def query_memory(
    request: Request,
    form_data: QueryMemoryForm,
    user=Depends(get_verified_user),
):
    # NOTE: We intentionally do NOT use Depends(get_session) here.
    # Database operations (get_memories_by_user_id) manage their own short-lived sessions.
    # This prevents holding a connection during EMBEDDING_FUNCTION()
    # which makes external embedding API calls (1-5+ seconds).
    if not request.app.state.config.ENABLE_MEMORIES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    if not has_permission(user.id, 'features.memories', request.app.state.config.USER_PERMISSIONS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    memories = Memories.get_enabled_memories_by_user_id(user.id)
    if not memories:
        raise HTTPException(status_code=404, detail='No memories found for user')

    vector = await request.app.state.EMBEDDING_FUNCTION(form_data.content, user=user)

    results = VECTOR_DB_CLIENT.search(
        collection_name=f'user-memory-{user.id}',
        vectors=[vector],
        limit=form_data.k,
    )

    if form_data.kind and getattr(results, 'metadatas', None):
        filtered_documents = []
        filtered_metadatas = []
        filtered_ids = []
        for idx, metadata in enumerate(results.metadatas[0]):
            if metadata.get('kind') == form_data.kind:
                filtered_documents.append(results.documents[0][idx])
                filtered_metadatas.append(metadata)
                filtered_ids.append(results.ids[0][idx])
        results.documents = [filtered_documents]
        results.metadatas = [filtered_metadatas]
        results.ids = [filtered_ids]

    return results


############################
# ResetMemoryFromVectorDB
############################
@router.post('/reset', response_model=bool)
async def reset_memory_from_vector_db(
    request: Request,
    user=Depends(get_verified_user),
):
    """Reset user's memory vector embeddings.

    CRITICAL: We intentionally do NOT use Depends(get_session) here.
    This endpoint generates embeddings for ALL user memories in parallel using
    asyncio.gather(). A user with 100 memories would trigger 100 embedding API
    calls simultaneously. With a session held, this could block a connection
    for MINUTES, completely exhausting the connection pool.
    """
    if not request.app.state.config.ENABLE_MEMORIES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    if not has_permission(user.id, 'features.memories', request.app.state.config.USER_PERMISSIONS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    VECTOR_DB_CLIENT.delete_collection(f'user-memory-{user.id}')

    memories = Memories.get_enabled_memories_by_user_id(user.id)

    # Generate vectors in parallel
    vectors = await asyncio.gather(
        *[request.app.state.EMBEDDING_FUNCTION(memory.content, user=user) for memory in memories]
    )

    VECTOR_DB_CLIENT.upsert(
        collection_name=f'user-memory-{user.id}',
        items=[
            {
                'id': memory.id,
                'text': memory.content,
                'vector': vectors[idx],
                'metadata': {
                    'created_at': memory.created_at,
                    'updated_at': memory.updated_at,
                    'kind': memory.kind,
                    'source': memory.source,
                },
            }
            for idx, memory in enumerate(memories)
        ],
    )

    return True


############################
# DeleteMemoriesByUserId
############################


@router.delete('/delete/user', response_model=bool)
async def delete_memory_by_user_id(
    request: Request,
    user=Depends(get_verified_user),
    db: Session = Depends(get_session),
):
    if not request.app.state.config.ENABLE_MEMORIES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    if not has_permission(user.id, 'features.memories', request.app.state.config.USER_PERMISSIONS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    result = Memories.delete_memories_by_user_id(user.id, db=db)

    if result:
        try:
            VECTOR_DB_CLIENT.delete_collection(f'user-memory-{user.id}')
        except Exception as e:
            log.error(e)
        return True

    return False


############################
# UpdateMemoryById
############################


@router.post('/{memory_id}/update', response_model=Optional[MemoryModel])
async def update_memory_by_id(
    memory_id: str,
    request: Request,
    form_data: MemoryUpdateModel,
    user=Depends(get_verified_user),
):
    # NOTE: We intentionally do NOT use Depends(get_session) here.
    # Database operations (update_memory_by_id_and_user_id) manage their own
    # short-lived sessions. This prevents holding a connection during
    # EMBEDDING_FUNCTION() which makes external API calls (1-5+ seconds).
    if not request.app.state.config.ENABLE_MEMORIES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    if not has_permission(user.id, 'features.memories', request.app.state.config.USER_PERMISSIONS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    existing_memory = Memories.get_memory_by_id(memory_id)
    if existing_memory is None or existing_memory.user_id != user.id:
        raise HTTPException(status_code=404, detail='Memory not found')

    memory = Memories.update_memory_by_id_and_user_id(
        memory_id,
        user.id,
        form_data.content if form_data.content is not None else existing_memory.content,
        kind=form_data.kind,
        source=form_data.source,
        enabled=form_data.enabled,
    )
    if memory is None:
        raise HTTPException(status_code=404, detail='Memory not found')

    if not memory.enabled:
        try:
            VECTOR_DB_CLIENT.delete(collection_name=f'user-memory-{user.id}', ids=[memory_id])
        except Exception as e:
            log.error(e)
        return memory

    if form_data.content is not None or form_data.kind is not None or form_data.source is not None:
        vector = await request.app.state.EMBEDDING_FUNCTION(memory.content, user=user)

        VECTOR_DB_CLIENT.upsert(
            collection_name=f'user-memory-{user.id}',
            items=[
                {
                    'id': memory.id,
                    'text': memory.content,
                    'vector': vector,
                    'metadata': {
                        'created_at': memory.created_at,
                        'updated_at': memory.updated_at,
                        'kind': memory.kind,
                        'source': memory.source,
                    },
                }
            ],
        )

    return memory


############################
# DeleteMemoryById
############################


@router.delete('/{memory_id}', response_model=bool)
async def delete_memory_by_id(
    memory_id: str,
    request: Request,
    user=Depends(get_verified_user),
    db: Session = Depends(get_session),
):
    if not request.app.state.config.ENABLE_MEMORIES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    if not has_permission(user.id, 'features.memories', request.app.state.config.USER_PERMISSIONS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    result = Memories.delete_memory_by_id_and_user_id(memory_id, user.id, db=db)

    if result:
        VECTOR_DB_CLIENT.delete(collection_name=f'user-memory-{user.id}', ids=[memory_id])
        return True

    return False


@router.get('/preferences', response_model=MemoryPreference)
async def get_memory_preferences(user=Depends(get_verified_user)):
    return get_memory_preference(user.id)


@router.post('/preferences/update', response_model=MemoryPreference)
async def update_memory_preferences(form_data: MemoryPreference, user=Depends(get_verified_user)):
    return update_memory_preference(user.id, form_data)
