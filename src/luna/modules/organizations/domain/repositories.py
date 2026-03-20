from typing import Protocol

from luna.modules.common.domain.entities import BoundingBox
from luna.modules.common.domain.entities import Organization


class OrganizationRepository(Protocol):
    async def get_by_id(self, organization_id: int) -> Organization | None: ...

    async def search_by_name(self, query: str) -> list[Organization]: ...

    async def list_by_building_id(self, building_id: int) -> list[Organization]: ...

    async def list_by_activity_ids(
        self, activity_ids: list[int]
    ) -> list[Organization]: ...

    async def search_by_location(
        self,
        *,
        latitude: float | None,
        longitude: float | None,
        radius_m: float | None,
        bounding_box: BoundingBox | None,
    ) -> list[Organization]: ...
