from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from luna.api.router import api_router
from luna.core.config import get_settings
from luna.core.security import authorize_api_key
from luna.shared.exceptions import BadRequestError, NotFoundError

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    openapi_url=settings.openapi_url,
    description="REST API для справочника организаций, зданий и видов деятельности.",
)


@app.exception_handler(NotFoundError)
async def handle_not_found(_: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": exc.message})


@app.exception_handler(BadRequestError)
async def handle_bad_request(_: Request, exc: BadRequestError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": exc.message})


app.include_router(
    api_router,
    prefix=settings.api_v1_prefix,
    dependencies=[Depends(authorize_api_key)],
)
