from typing import Protocol

from luna.modules.common.domain.entities import Building


class BuildingRepository(Protocol):
    async def list_all(self) -> list[Building]: ...

    async def get_by_id(self, building_id: int) -> Building | None: ...
