import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_buildings_returns_seeded_data(client: AsyncClient) -> None:
    response = await client.get("/api/v1/buildings")

    assert response.status_code == 200
    payload = response.json()
    assert [item["address"] for item in payload] == [
        "г. Москва, ул. Ленина 1",
        "г. Москва, ул. Тверская 7",
    ]


@pytest.mark.asyncio
async def test_search_by_activity_includes_descendants(
    client: AsyncClient,
) -> None:
    response = await client.get(
        "/api/v1/organizations/search/by-activity",
        params={"name": "Еда", "include_descendants": "true"},
    )

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["Молоко Плюс"]


@pytest.mark.asyncio
async def test_get_organization_by_id_returns_404_for_missing_record(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/v1/organizations/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Organization not found"}


@pytest.mark.asyncio
async def test_search_by_location_requires_search_shape(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/v1/organizations/search/by-location")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_api_key_is_required(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/buildings",
        headers={"X-API-Key": "wrong-key"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid API key"}
