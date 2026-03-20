from fastapi import HTTPException
from fastapi import Security
from fastapi.security import APIKeyHeader

from luna.core.config import get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def authorize_api_key(api_key: str | None = Security(api_key_header)) -> str | None:
    expected = get_settings().api_key
    
    if api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")
        
    return api_key
