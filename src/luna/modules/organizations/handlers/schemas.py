from fastapi import HTTPException
from fastapi import Query
from pydantic import BaseModel, ValidationError, model_validator

from luna.modules.common.domain.entities import (
    Activity,
    BoundingBox,
    Building,
    Organization,
)


class ActivityResponse(BaseModel):
    id: int
    name: str
    parent_id: int | None

    @classmethod
    def from_entity(cls, activity: Activity) -> "ActivityResponse":
        return cls(id=activity.id, name=activity.name, parent_id=activity.parent_id)


class BuildingResponse(BaseModel):
    id: int
    address: str
    latitude: float
    longitude: float

    @classmethod
    def from_entity(cls, building: Building) -> "BuildingResponse":
        return cls(
            id=building.id,
            address=building.address,
            latitude=building.latitude,
            longitude=building.longitude,
        )


class OrganizationResponse(BaseModel):
    id: int
    name: str
    building: BuildingResponse
    phones: list[str]
    activities: list[ActivityResponse]

    @classmethod
    def from_entity(cls, organization: Organization) -> "OrganizationResponse":
        return cls(
            id=organization.id,
            name=organization.name,
            building=BuildingResponse.from_entity(organization.building),
            phones=organization.phones,
            activities=[
                ActivityResponse.from_entity(activity)
                for activity in organization.activities
            ],
        )


class LocationSearchQuery(BaseModel):
    lat: float | None = Query(default=None, ge=-90, le=90)
    lon: float | None = Query(default=None, ge=-180, le=180)
    radius_m: float | None = Query(default=None, gt=0)
    min_lat: float | None = Query(default=None, ge=-90, le=90)
    max_lat: float | None = Query(default=None, ge=-90, le=90)
    min_lon: float | None = Query(default=None, ge=-180, le=180)
    max_lon: float | None = Query(default=None, ge=-180, le=180)

    @model_validator(mode="after")
    def validate_query(self) -> "LocationSearchQuery":
        has_radius = self.radius_m is not None
        has_bbox = None not in (self.min_lat, self.max_lat, self.min_lon, self.max_lon)

        if has_radius and has_bbox:
            raise ValueError("Use either radius search or bounding box search")

        if not has_radius and not has_bbox:
            raise ValueError("Provide either radius search or bounding box search")
        if has_radius and (self.lat is None or self.lon is None):
            raise ValueError("lat and lon are required for radius search")

        return self

    def to_bounding_box(self) -> BoundingBox | None:
        if (
            self.min_lat is None
            or self.max_lat is None
            or self.min_lon is None
            or self.max_lon is None
        ):
            return None

        return BoundingBox.create(
            min_lat=self.min_lat,
            max_lat=self.max_lat,
            min_lon=self.min_lon,
            max_lon=self.max_lon,
        )


def build_location_search_query(
    lat: float | None = Query(default=None, ge=-90, le=90),
    lon: float | None = Query(default=None, ge=-180, le=180),
    radius_m: float | None = Query(default=None, gt=0),
    min_lat: float | None = Query(default=None, ge=-90, le=90),
    max_lat: float | None = Query(default=None, ge=-90, le=90),
    min_lon: float | None = Query(default=None, ge=-180, le=180),
    max_lon: float | None = Query(default=None, ge=-180, le=180),
) -> LocationSearchQuery:
    try:
        return LocationSearchQuery(
            lat=lat,
            lon=lon,
            radius_m=radius_m,
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon,
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=exc.errors(include_context=False),
        ) from exc
