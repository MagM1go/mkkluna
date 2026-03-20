import math

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select

from luna.db.models import BuildingModel
from luna.db.models import OrganizationActivityModel
from luna.db.models import OrganizationModel
from luna.modules.common.domain.entities import Activity
from luna.modules.common.domain.entities import BoundingBox
from luna.modules.common.domain.entities import Building
from luna.modules.common.domain.entities import Organization


class SqlAlchemyOrganizationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, organization_id: int) -> Organization | None:
        statement = self._base_statement().where(
            OrganizationModel.id == organization_id
        )
        model = (await self._session.scalars(statement)).unique().first()
        if model is None:
            return None

        return self._to_entity(model)

    async def search_by_name(self, query: str) -> list[Organization]:
        normalized_query = query.casefold()
        statement = self._base_statement()
        models = (
            await self._session.scalars(statement.order_by(OrganizationModel.name.asc()))
        ).unique().all()
        return [
            self._to_entity(model)
            for model in models
            if normalized_query in model.name.casefold()
        ]

    async def list_by_building_id(self, building_id: int) -> list[Organization]:
        statement = self._base_statement().where(
            OrganizationModel.building_id == building_id
        )
        models = (
            await self._session.scalars(statement.order_by(OrganizationModel.name.asc()))
        ).unique().all()
        return [self._to_entity(model) for model in models]

    async def list_by_activity_ids(self, activity_ids: list[int]) -> list[Organization]:
        if not activity_ids:
            return []

        statement = (
            self._base_statement()
            .join(
                OrganizationActivityModel,
                OrganizationActivityModel.organization_id == OrganizationModel.id,
            )
            .where(OrganizationActivityModel.activity_id.in_(activity_ids))
            .order_by(OrganizationModel.name.asc())
        )
        models = (await self._session.scalars(statement)).unique().all()
        return [self._to_entity(model) for model in models]

    async def search_by_location(
        self,
        *,
        latitude: float | None,
        longitude: float | None,
        radius_m: float | None,
        bounding_box: BoundingBox | None,
    ) -> list[Organization]:
        statement = self._base_statement().join(
            BuildingModel, BuildingModel.id == OrganizationModel.building_id
        )

        if bounding_box is not None:
            statement = statement.where(
                BuildingModel.latitude.between(
                    bounding_box.min_lat, bounding_box.max_lat
                ),
                BuildingModel.longitude.between(
                    bounding_box.min_lon, bounding_box.max_lon
                ),
            )
            models = (
                await self._session.scalars(
                    statement.order_by(OrganizationModel.name.asc())
                )
            ).unique().all()
            return [self._to_entity(model) for model in models]

        if latitude is None or longitude is None or radius_m is None:
            return []

        lat_delta = radius_m / 111_320
        safe_cosine = max(math.cos(math.radians(latitude)), 0.01)
        lon_delta = radius_m / (111_320 * safe_cosine)

        candidate_statement = statement.where(
            BuildingModel.latitude.between(latitude - lat_delta, latitude + lat_delta),
            BuildingModel.longitude.between(
                longitude - lon_delta, longitude + lon_delta
            ),
        )
        candidates = (
            await self._session.scalars(
                candidate_statement.order_by(OrganizationModel.name.asc())
            )
        ).unique().all()

        return [
            self._to_entity(model)
            for model in candidates
            if self._distance_m(
                latitude, longitude, model.building.latitude, model.building.longitude
            )
            <= radius_m
        ]

    @staticmethod
    def _distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        radius = 6_371_000
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (
            math.sin(d_lat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(d_lon / 2) ** 2
        )
        return 2 * radius * math.asin(math.sqrt(a))

    @staticmethod
    def _base_statement() -> Select[tuple[OrganizationModel]]:
        return select(OrganizationModel).options(
            joinedload(OrganizationModel.building),
            selectinload(OrganizationModel.phones),
            selectinload(OrganizationModel.activity_links).joinedload(
                OrganizationActivityModel.activity
            ),
        )

    @staticmethod
    def _to_entity(model: OrganizationModel) -> Organization:
        building = Building(
            id=model.building.id,
            address=model.building.address,
            latitude=model.building.latitude,
            longitude=model.building.longitude,
        )
        phones = sorted(phone.phone for phone in model.phones)
        activities = sorted(
            [
                Activity(
                    id=link.activity.id,
                    name=link.activity.name,
                    parent_id=link.activity.parent_id,
                )
                for link in model.activity_links
            ],
            key=lambda item: item.name.lower(),
        )
        return Organization(
            id=model.id,
            name=model.name,
            building=building,
            phones=phones,
            activities=activities,
        )
