import asyncio
from typing import Any

from sqlalchemy import select

from luna.core.database import SessionLocal
from luna.db.models import (
    ActivityModel,
    BuildingModel,
    OrganizationActivityModel,
    OrganizationModel,
    OrganizationPhoneModel,
)

BUILDINGS: list[dict[str, Any]] = [
    {
        "address": "г. Москва, ул. Ленина 1, офис 3",
        "latitude": 55.751244,
        "longitude": 37.618423,
    },
    {
        "address": "г. Москва, ул. Блюхера 32/1",
        "latitude": 55.761244,
        "longitude": 37.628423,
    },
    {
        "address": "г. Москва, пр. Мира 14",
        "latitude": 55.779734,
        "longitude": 37.632111,
    },
    {
        "address": "г. Москва, ул. Тверская 7",
        "latitude": 55.764167,
        "longitude": 37.605278,
    },
]

ACTIVITY_TREE: list[dict[str, Any]] = [
    {
        "name": "Еда",
        "children": [
            {"name": "Мясная продукция", "children": []},
            {"name": "Молочная продукция", "children": []},
        ],
    },
    {
        "name": "Автомобили",
        "children": [
            {"name": "Грузовые", "children": []},
            {
                "name": "Легковые",
                "children": [
                    {"name": "Запчасти", "children": []},
                    {"name": "Аксессуары", "children": []},
                ],
            },
        ],
    },
    {
        "name": "Технологии",
        "children": [
            {"name": "Софт", "children": []},
            {"name": "Железо", "children": []},
        ],
    },
]

ORGANIZATIONS: list[dict[str, Any]] = [
    {
        "name": "ООО Рога и Копыта",
        "building": "г. Москва, ул. Блюхера 32/1",
        "phones": ["2-222-222", "3-333-333", "8-923-666-13-13"],
        "activities": ["Молочная продукция", "Мясная продукция"],
    },
    {
        "name": "Молоко Плюс",
        "building": "г. Москва, ул. Ленина 1, офис 3",
        "phones": ["8-800-100-10-10", "8-800-100-10-11"],
        "activities": ["Молочная продукция"],
    },
    {
        "name": "Truck Service Hub",
        "building": "г. Москва, пр. Мира 14",
        "phones": ["8-495-700-00-01"],
        "activities": ["Грузовые", "Запчасти"],
    },
    {
        "name": "Auto Style Market",
        "building": "г. Москва, ул. Тверская 7",
        "phones": ["8-495-700-00-02", "8-495-700-00-03"],
        "activities": ["Аксессуары", "Легковые"],
    },
    {
        "name": "Soft Atlas",
        "building": "г. Москва, ул. Ленина 1, офис 3",
        "phones": ["8-495-700-00-04"],
        "activities": ["Софт"],
    },
]


def validate_activity_depth(tree: list[dict[str, Any]], depth: int = 1) -> None:
    for node in tree:
        if depth > 3:
            raise ValueError("Activity depth must not exceed 3 levels")

        validate_activity_depth(node.get("children", []), depth + 1)


async def seed() -> None:
    validate_activity_depth(ACTIVITY_TREE)

    async with SessionLocal() as session:
        existing_building = await session.scalar(select(BuildingModel.id).limit(1))
        if existing_building is not None:
            return

        building_map: dict[str, BuildingModel] = {}
        for payload in BUILDINGS:
            building = BuildingModel(**payload)
            session.add(building)
            await session.flush()
            building_map[building.address] = building

        activity_map: dict[str, ActivityModel] = {}

        async def add_activity(
            nodes: list[dict[str, Any]], parent: ActivityModel | None = None
        ) -> None:
            for node in nodes:
                activity = ActivityModel(name=node["name"], parent=parent)
                session.add(activity)
                await session.flush()
                activity_map[activity.name] = activity
                await add_activity(node.get("children", []), activity)

        await add_activity(ACTIVITY_TREE)

        for payload in ORGANIZATIONS:
            organization = OrganizationModel(
                name=payload["name"],
                building=building_map[payload["building"]],
            )
            session.add(organization)
            await session.flush()

            for phone in payload["phones"]:
                session.add(
                    OrganizationPhoneModel(organization=organization, phone=phone)
                )

            for activity_name in payload["activities"]:
                session.add(
                    OrganizationActivityModel(
                        organization=organization,
                        activity=activity_map[activity_name],
                    )
                )

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
