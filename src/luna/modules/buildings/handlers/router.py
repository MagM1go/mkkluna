from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from luna.core.database import get_session
from luna.modules.buildings.handlers.schemas import BuildingResponse
from luna.modules.buildings.repository import SqlAlchemyBuildingRepository
from luna.modules.buildings.service.use_cases import ListBuildingsService
from luna.modules.organizations.handlers.schemas import OrganizationResponse
from luna.modules.organizations.repository import SqlAlchemyOrganizationRepository
from luna.modules.organizations.service.use_cases import ListOrganizationsByBuildingService

router = APIRouter(prefix="/buildings", tags=["Buildings"])


def get_list_buildings_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ListBuildingsService:
    return ListBuildingsService(SqlAlchemyBuildingRepository(session))


def get_list_organizations_by_building_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ListOrganizationsByBuildingService:
    return ListOrganizationsByBuildingService(
        building_repository=SqlAlchemyBuildingRepository(session),
        organization_repository=SqlAlchemyOrganizationRepository(session),
    )


@router.get("", response_model=list[BuildingResponse], summary="Список зданий")
async def list_buildings(
    service: Annotated[ListBuildingsService, Depends(get_list_buildings_service)],
) -> list[BuildingResponse]:
    buildings = await service.execute()
    return [BuildingResponse.from_entity(building) for building in buildings]


@router.get(
    "/{building_id}/organizations",
    response_model=list[OrganizationResponse],
    summary="Организации в конкретном здании",
)
async def list_organizations_by_building(
    building_id: int,
    service: Annotated[
        ListOrganizationsByBuildingService,
        Depends(get_list_organizations_by_building_service),
    ],
) -> list[OrganizationResponse]:
    organizations = await service.execute(building_id)
    return [OrganizationResponse.from_entity(org) for org in organizations]
