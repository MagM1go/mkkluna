from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession

from luna.core.database import get_session
from luna.modules.activities.repository import SqlAlchemyActivityRepository
from luna.modules.organizations.handlers.schemas import build_location_search_query
from luna.modules.organizations.handlers.schemas import LocationSearchQuery
from luna.modules.organizations.handlers.schemas import OrganizationResponse
from luna.modules.organizations.repository import SqlAlchemyOrganizationRepository
from luna.modules.organizations.service.use_cases import GetOrganizationByIdService
from luna.modules.organizations.service.use_cases import SearchOrganizationsByActivityNameService
from luna.modules.organizations.service.use_cases import SearchOrganizationsByLocationService
from luna.modules.organizations.service.use_cases import SearchOrganizationsByNameService

router = APIRouter(prefix="/organizations", tags=["Organizations"])


def get_organization_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SqlAlchemyOrganizationRepository:
    return SqlAlchemyOrganizationRepository(session)


def get_get_organization_by_id_service(
    repository: Annotated[
        SqlAlchemyOrganizationRepository, Depends(get_organization_repository)
    ],
) -> GetOrganizationByIdService:
    return GetOrganizationByIdService(repository)


def get_search_by_name_service(
    repository: Annotated[
        SqlAlchemyOrganizationRepository, Depends(get_organization_repository)
    ],
) -> SearchOrganizationsByNameService:
    return SearchOrganizationsByNameService(repository)


def get_search_by_activity_name_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    repository: Annotated[
        SqlAlchemyOrganizationRepository, Depends(get_organization_repository)
    ],
) -> SearchOrganizationsByActivityNameService:
    return SearchOrganizationsByActivityNameService(
        activity_repository=SqlAlchemyActivityRepository(session),
        organization_repository=repository,
    )


def get_search_by_location_service(
    repository: Annotated[
        SqlAlchemyOrganizationRepository, Depends(get_organization_repository)
    ],
) -> SearchOrganizationsByLocationService:
    return SearchOrganizationsByLocationService(repository)


@router.get(
    "/search/by-name",
    response_model=list[OrganizationResponse],
    summary="Поиск организаций по названию",
)
async def search_organizations_by_name(
    query: str = Query(..., min_length=1),
    service: SearchOrganizationsByNameService = Depends(get_search_by_name_service),
) -> list[OrganizationResponse]:
    organizations = await service.execute(query)
    return [OrganizationResponse.from_entity(org) for org in organizations]


@router.get(
    "/search/by-activity",
    response_model=list[OrganizationResponse],
    summary="Поиск организаций по виду деятельности",
)
async def search_organizations_by_activity(
    name: str = Query(..., min_length=1),
    include_descendants: bool = Query(default=True),
    service: SearchOrganizationsByActivityNameService = Depends(
        get_search_by_activity_name_service
    ),
) -> list[OrganizationResponse]:
    organizations = await service.execute(
        name=name,
        include_descendants=include_descendants,
    )
    return [OrganizationResponse.from_entity(org) for org in organizations]


@router.get(
    "/search/by-location",
    response_model=list[OrganizationResponse],
    summary="Поиск организаций по радиусу или прямоугольной области",
)
async def search_organizations_by_location(
    query: Annotated[LocationSearchQuery, Depends(build_location_search_query)],
    service: SearchOrganizationsByLocationService = Depends(
        get_search_by_location_service
    ),
) -> list[OrganizationResponse]:
    organizations = await service.execute(
        latitude=query.lat,
        longitude=query.lon,
        radius_m=query.radius_m,
        bounding_box=query.to_bounding_box(),
    )
    return [OrganizationResponse.from_entity(org) for org in organizations]


@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
    summary="Информация об организации по идентификатору",
)
async def get_organization_by_id(
    organization_id: int,
    service: GetOrganizationByIdService = Depends(get_get_organization_by_id_service),
) -> OrganizationResponse:
    organization = await service.execute(organization_id)
    return OrganizationResponse.from_entity(organization)
