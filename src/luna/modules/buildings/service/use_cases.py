from luna.modules.buildings.domain.repositories import BuildingRepository
from luna.modules.common.domain.entities import Building


class ListBuildingsService:
    def __init__(self, building_repository: BuildingRepository) -> None:
        self._building_repository = building_repository

    async def execute(self) -> list[Building]:
        return await self._building_repository.list_all()
