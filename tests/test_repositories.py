import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker

from luna.modules.activities.repository import SqlAlchemyActivityRepository
from luna.modules.organizations.repository import SqlAlchemyOrganizationRepository


@pytest.mark.asyncio
async def test_activity_repository_returns_descendant_branch_ids(
    seeded_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with seeded_session_factory() as session:
        repository = SqlAlchemyActivityRepository(session)

        branch_ids = await repository.get_branch_ids_by_name("Еда", max_depth=3)

    assert len(branch_ids) == 2


@pytest.mark.asyncio
async def test_organization_repository_filters_by_radius(
    seeded_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with seeded_session_factory() as session:
        repository = SqlAlchemyOrganizationRepository(session)

        organizations = await repository.search_by_location(
            latitude=55.751244,
            longitude=37.618423,
            radius_m=500,
            bounding_box=None,
        )

    assert [organization.name for organization in organizations] == ["Молоко Плюс"]
