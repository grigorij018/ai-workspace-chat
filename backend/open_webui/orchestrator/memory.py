from open_webui.models.users import Users
from open_webui.orchestrator.schemas import MemoryPreference


DEFAULT_MEMORY_PREFERENCE = MemoryPreference(enabled=True, auto_store=True)


def get_memory_preference(user_id: str) -> MemoryPreference:
    user = Users.get_user_by_id(user_id)
    if not user:
        return DEFAULT_MEMORY_PREFERENCE

    settings = user.settings or {}
    memory = settings.get('memory') or {}
    return MemoryPreference(
        enabled=memory.get('enabled', DEFAULT_MEMORY_PREFERENCE.enabled),
        auto_store=memory.get('auto_store', DEFAULT_MEMORY_PREFERENCE.auto_store),
    )


def update_memory_preference(user_id: str, preference: MemoryPreference) -> MemoryPreference:
    Users.update_user_settings_by_id(
        user_id,
        {'memory': preference.model_dump()},
    )
    return get_memory_preference(user_id)
