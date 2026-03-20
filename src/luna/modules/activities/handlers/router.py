from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession

from luna.core.database import get_session
from luna.modules.activities.handlers.schemas import ActivityTreeNodeResponse
from luna.modules.activities.repository import SqlAlchemyActivityRepository
from luna.modules.activities.service.use_cases import ListActivityTreeService
from luna.modules.organizations.handlers.schemas import OrganizationResponse
from luna.modules.organizations.repository import SqlAlchemyOrganizationRepository
from luna.modules.organizations.service.use_cases import ListOrganizationsByActivityService

router = APIRouter(prefix="/activities", tags=["Activities"])


def get_list_activity_tree_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ListActivityTreeService:
    return ListActivityTreeService(SqlAlchemyActivityRepository(session))


def get_list_organizations_by_activity_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ListOrganizationsByActivityService:
    return ListOrganizationsByActivityService(
        activity_repository=SqlAlchemyActivityRepository(session),
        organization_repository=SqlAlchemyOrganizationRepository(session),
    )


@router.get(
    "/tree",
    response_model=list[ActivityTreeNodeResponse],
    summary="Дерево деятельностей",
)
async def list_activity_tree(
    service: Annotated[ListActivityTreeService, Depends(get_list_activity_tree_service)],
) -> list[ActivityTreeNodeResponse]:
    activity_tree = await service.execute()
    return [ActivityTreeNodeResponse.from_entity(node) for node in activity_tree]


@router.get(
    "/{activity_id}/organizations",
    response_model=list[OrganizationResponse],
    summary="Организации по виду деятельности",
)
async def list_organizations_by_activity(
    activity_id: int,
    service: Annotated[
        ListOrganizationsByActivityService,
        Depends(get_list_organizations_by_activity_service),
    ],
    include_descendants: bool = Query(default=False),
) -> list[OrganizationResponse]:
    organizations = await service.execute(
        activity_id=activity_id,
        include_descendants=include_descendants,
    )
    return [OrganizationResponse.from_entity(org) for org in organizations]
