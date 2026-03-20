import os
from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./.pytest-bootstrap.db")

from luna.core.database import Base
from luna.core.database import get_session
from luna.db.models import ActivityModel
from luna.db.models import BuildingModel
from luna.db.models import OrganizationActivityModel
from luna.db.models import OrganizationModel
from luna.db.models import OrganizationPhoneModel
from luna.main import app


@pytest_asyncio.fixture
async def engine(tmp_path) -> AsyncIterator[AsyncEngine]:
    database_path = tmp_path / "test.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{database_path}")

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def seeded_session_factory(
    session_factory: async_sessionmaker[AsyncSession],
) -> async_sessionmaker[AsyncSession]:
    async with session_factory() as session:
        building_1 = BuildingModel(
            address="г. Москва, ул. Ленина 1",
            latitude=55.751244,
            longitude=37.618423,
        )
        building_2 = BuildingModel(
            address="г. Москва, ул. Тверская 7",
            latitude=55.764167,
            longitude=37.605278,
        )

        food = ActivityModel(name="Еда", parent_id=None)
        dairy = ActivityModel(name="Молочная продукция", parent=food)
        auto = ActivityModel(name="Автомобили", parent_id=None)

        milk_plus = OrganizationModel(name="Молоко Плюс", building=building_1)
        auto_style = OrganizationModel(name="Auto Style Market", building=building_2)

        session.add_all(
            [
                building_1,
                building_2,
                food,
                dairy,
                auto,
                milk_plus,
                auto_style,
            ]
        )
        await session.flush()

        session.add_all(
            [
                OrganizationPhoneModel(
                    organization=milk_plus, phone="8-800-100-10-10"
                ),
                OrganizationPhoneModel(
                    organization=auto_style, phone="8-495-700-00-02"
                ),
                OrganizationActivityModel(
                    organization=milk_plus,
                    activity=dairy,
                ),
                OrganizationActivityModel(
                    organization=auto_style,
                    activity=auto,
                ),
            ]
        )
        await session.commit()

    return session_factory


@pytest_asyncio.fixture
async def client(
    seeded_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncClient]:
    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with seeded_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
        headers={"X-API-Key": "super-secret-api-key"},
    ) as http_client:
        yield http_client

    app.dependency_overrides.clear()
