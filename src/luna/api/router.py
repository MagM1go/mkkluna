from fastapi import APIRouter

from luna.modules.activities.handlers.router import router as activities_router
from luna.modules.buildings.handlers.router import router as buildings_router
from luna.modules.organizations.handlers.router import router as organizations_router

api_router = APIRouter()
api_router.include_router(buildings_router)
api_router.include_router(activities_router)
api_router.include_router(organizations_router)
