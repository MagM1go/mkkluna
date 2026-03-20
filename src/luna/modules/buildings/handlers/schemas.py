from pydantic import BaseModel

from luna.modules.common.domain.entities import Building


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
