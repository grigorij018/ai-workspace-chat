from openai import AsyncOpenAI

from open_webui.config import MWS_API_KEY, MWS_BASE_URL


def get_mws_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=MWS_API_KEY,
        base_url=MWS_BASE_URL,
    )
