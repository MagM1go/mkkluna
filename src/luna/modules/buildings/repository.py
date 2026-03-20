from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from luna.db.models import BuildingModel
from luna.modules.common.domain.entities import Building


class SqlAlchemyBuildingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[Building]:
        result = await self._session.scalars(
            select(BuildingModel).order_by(BuildingModel.address.asc())
        )
        return [self._to_entity(model) for model in result.all()]

    async def get_by_id(self, building_id: int) -> Building | None:
        model = await self._session.get(BuildingModel, building_id)
        if model is None:
            return None

        return self._to_entity(model)

    @staticmethod
    def _to_entity(model: BuildingModel) -> Building:
        return Building(
            id=model.id,
            address=model.address,
            latitude=model.latitude,
            longitude=model.longitude,
        )
