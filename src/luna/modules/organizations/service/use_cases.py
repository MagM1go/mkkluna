from luna.modules.activities.domain.repositories import ActivityRepository
from luna.modules.buildings.domain.repositories import BuildingRepository
from luna.modules.common.domain.entities import BoundingBox, Organization
from luna.modules.organizations.domain.repositories import OrganizationRepository
from luna.shared.exceptions import BadRequestError, NotFoundError


class GetOrganizationByIdService:
    def __init__(self, organization_repository: OrganizationRepository) -> None:
        self._organization_repository = organization_repository

    async def execute(self, organization_id: int) -> Organization:
        organization = await self._organization_repository.get_by_id(organization_id)
        if organization is None:
            raise NotFoundError("Organization not found")

        return organization


class SearchOrganizationsByNameService:
    def __init__(self, organization_repository: OrganizationRepository) -> None:
        self._organization_repository = organization_repository

    async def execute(self, query: str) -> list[Organization]:
        if not query.strip():
            raise BadRequestError("query must not be empty")

        return await self._organization_repository.search_by_name(query.strip())


class ListOrganizationsByBuildingService:
    def __init__(
        self,
        building_repository: BuildingRepository,
        organization_repository: OrganizationRepository,
    ) -> None:
        self._building_repository = building_repository
        self._organization_repository = organization_repository

    async def execute(self, building_id: int) -> list[Organization]:
        building = await self._building_repository.get_by_id(building_id)
        if building is None:
            raise NotFoundError("Building not found")
        return await self._organization_repository.list_by_building_id(building_id)


class ListOrganizationsByActivityService:
    def __init__(
        self,
        activity_repository: ActivityRepository,
        organization_repository: OrganizationRepository,
    ) -> None:
        self._activity_repository = activity_repository
        self._organization_repository = organization_repository

    async def execute(
        self, activity_id: int, include_descendants: bool
    ) -> list[Organization]:
        activity = await self._activity_repository.get_by_id(activity_id)
        if activity is None:
            raise NotFoundError("Activity not found")
        if include_descendants:
            activity_ids = await self._activity_repository.get_branch_ids(
                activity_id, max_depth=3
            )
        else:
            activity_ids = [activity_id]
        return await self._organization_repository.list_by_activity_ids(activity_ids)


class SearchOrganizationsByActivityNameService:
    def __init__(
        self,
        activity_repository: ActivityRepository,
        organization_repository: OrganizationRepository,
    ) -> None:
        self._activity_repository = activity_repository
        self._organization_repository = organization_repository

    async def execute(
        self, name: str, include_descendants: bool
    ) -> list[Organization]:
        normalized_name = name.strip()
        if not normalized_name:
            raise BadRequestError("name must not be empty")

        max_depth = 3 if include_descendants else 1
        activity_ids = await self._activity_repository.get_branch_ids_by_name(
            normalized_name, max_depth=max_depth
        )
        if not activity_ids:
            raise NotFoundError("Activity not found")

        return await self._organization_repository.list_by_activity_ids(activity_ids)


class SearchOrganizationsByLocationService:
    def __init__(self, organization_repository: OrganizationRepository) -> None:
        self._organization_repository = organization_repository

    async def execute(
        self,
        *,
        latitude: float | None,
        longitude: float | None,
        radius_m: float | None,
        bounding_box: BoundingBox | None,
    ) -> list[Organization]:
        if bounding_box is None and radius_m is None:
            raise BadRequestError(
                "Either radius search or bounding box search must be provided"
            )

        if bounding_box is not None and radius_m is not None:
            raise BadRequestError(
                "Use either radius search or bounding box search, not both"
            )

        if radius_m is not None and (latitude is None or longitude is None):
            raise BadRequestError("lat and lon are required for radius search")

        return await self._organization_repository.search_by_location(
            latitude=latitude,
            longitude=longitude,
            radius_m=radius_m,
            bounding_box=bounding_box,
        )
