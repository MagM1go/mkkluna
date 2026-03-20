from dataclasses import dataclass
from typing import Self

from luna.shared.exceptions import BadRequestError


@dataclass(frozen=True)
class Building:
    id: int
    address: str
    latitude: float
    longitude: float


@dataclass(frozen=True)
class Activity:
    id: int
    name: str
    parent_id: int | None


@dataclass(frozen=True)
class ActivityTreeNode:
    id: int
    name: str
    parent_id: int | None
    children: list["ActivityTreeNode"]


@dataclass(frozen=True)
class Organization:
    id: int
    name: str
    building: Building
    phones: list[str]
    activities: list[Activity]


@dataclass(frozen=True)
class BoundingBox:
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float

    @classmethod
    def create(cls, min_lat: float, max_lat: float, min_lon: float, max_lon: float) -> Self:
        if min_lat > max_lat:
            raise BadRequestError("min_lat must be less than or equal to max_lat")
        if min_lon > max_lon:
            raise BadRequestError("min_lon must be less than or equal to max_lon")
        return cls(min_lat=min_lat, max_lat=max_lat, min_lon=min_lon, max_lon=max_lon)
