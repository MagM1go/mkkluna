import asyncio
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

API_KEY = "super-secret-api-key"
HOST = "127.0.0.1"
PORT = 8000


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _request(
    path: str,
    *,
    params: dict[str, Any] | None = None,
    api_key: str = API_KEY,
) -> tuple[int, Any]:
    query = f"?{urllib.parse.urlencode(params)}" if params else ""
    request = urllib.request.Request(
        f"http://{HOST}:{PORT}{path}{query}",
        headers={"X-API-Key": api_key},
    )

    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            payload = response.read().decode(charset)
            return response.status, json.loads(payload)
    except urllib.error.HTTPError as exc:
        charset = exc.headers.get_content_charset() or "utf-8"
        payload = exc.read().decode(charset)
        return exc.code, json.loads(payload)


async def _prepare_database(database_url: str) -> None:
    os.environ["DATABASE_URL"] = database_url

    from sqlalchemy.ext.asyncio import create_async_engine

    from luna.core.database import Base
    from luna.seed import seed

    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    await engine.dispose()

    await seed()


def _wait_for_server(process: subprocess.Popen[str]) -> None:
    deadline = time.time() + 15
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Server exited early with code {process.returncode}")
        try:
            with socket.create_connection((HOST, PORT), timeout=0.5):
                return
        except OSError:
            time.sleep(0.2)

    raise TimeoutError(f"Server did not start on {HOST}:{PORT}")


def _run_checks() -> None:
    status, buildings = _request("/api/v1/buildings")
    _assert(status == 200, f"GET /buildings returned {status}")
    _assert(isinstance(buildings, list) and buildings, "Buildings list is empty")

    building_id = buildings[0]["id"]
    status, building_orgs = _request(f"/api/v1/buildings/{building_id}/organizations")
    _assert(
        status == 200, f"GET /buildings/{building_id}/organizations returned {status}"
    )
    _assert(
        isinstance(building_orgs, list) and building_orgs,
        "Organizations by building is empty",
    )

    status, activity_tree = _request("/api/v1/activities/tree")
    _assert(status == 200, f"GET /activities/tree returned {status}")
    _assert(isinstance(activity_tree, list) and activity_tree, "Activity tree is empty")

    def validate_depth(nodes: list[dict[str, Any]], depth: int = 1) -> None:
        for node in nodes:
            _assert(depth <= 3, f"Activity tree depth exceeded: {depth}")
            validate_depth(node["children"], depth + 1)

    validate_depth(activity_tree)

    food_node = next(node for node in activity_tree if node["name"] == "Еда")
    dairy_node = next(
        node for node in food_node["children"] if node["name"] == "Молочная продукция"
    )

    status, orgs_by_activity = _request(
        f"/api/v1/activities/{dairy_node['id']}/organizations"
    )
    _assert(
        status == 200,
        f"GET /activities/{dairy_node['id']}/organizations returned {status}",
    )
    _assert(
        any(item["name"] == "Молоко Плюс" for item in orgs_by_activity),
        "Expected organization not found for activity lookup",
    )

    status, by_name = _request(
        "/api/v1/organizations/search/by-name",
        params={"query": "молоко"},
    )
    _assert(status == 200, f"GET /organizations/search/by-name returned {status}")
    _assert(
        any(item["name"] == "Молоко Плюс" for item in by_name),
        "Search by name did not return expected organization",
    )

    status, by_activity_name = _request(
        "/api/v1/organizations/search/by-activity",
        params={"name": "Еда", "include_descendants": "true"},
    )
    _assert(
        status == 200,
        f"GET /organizations/search/by-activity returned {status}",
    )
    _assert(
        {item["name"] for item in by_activity_name}
        == {"Молоко Плюс", "ООО Рога и Копыта"},
        "Search by activity did not return expected descendant organizations",
    )

    status, by_radius = _request(
        "/api/v1/organizations/search/by-location",
        params={"lat": 55.751244, "lon": 37.618423, "radius_m": 500},
    )
    _assert(
        status == 200,
        f"GET /organizations/search/by-location radius returned {status}",
    )
    _assert(
        any(item["name"] == "Молоко Плюс" for item in by_radius),
        "Radius search did not return expected organization",
    )

    status, by_bbox = _request(
        "/api/v1/organizations/search/by-location",
        params={
            "min_lat": 55.74,
            "max_lat": 55.77,
            "min_lon": 37.60,
            "max_lon": 37.63,
        },
    )
    _assert(
        status == 200,
        f"GET /organizations/search/by-location bbox returned {status}",
    )
    _assert(
        isinstance(by_bbox, list) and by_bbox,
        "Bounding-box search returned no organizations",
    )

    organization_id = by_name[0]["id"]
    status, organization = _request(f"/api/v1/organizations/{organization_id}")
    _assert(status == 200, f"GET /organizations/{organization_id} returned {status}")
    _assert(
        organization["name"] == "Молоко Плюс",
        "Organization lookup returned unexpected record",
    )

    status, unauthorized = _request("/api/v1/buildings", api_key="wrong-key")
    _assert(status == 401, f"Unauthorized request returned {status}")
    _assert(
        unauthorized["detail"] == "Invalid API key", "Unexpected unauthorized response"
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="luna-smoke-") as tmpdir:
        db_path = Path(tmpdir) / "smoke.db"
        database_url = f"sqlite+aiosqlite:///{db_path}"

        asyncio.run(_prepare_database(database_url))

        env = os.environ.copy()
        env["DATABASE_URL"] = database_url
        env["API_KEY"] = API_KEY
        env["PYTHONPATH"] = str(Path.cwd() / "src")

        process = subprocess.Popen(
            [sys.executable, "-m", "luna"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        try:
            _wait_for_server(process)
            _run_checks()
            print("Smoke API test passed")
            return 0
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

            if process.stdout is not None:
                output = process.stdout.read().strip()
                if output:
                    print("--- server log ---")
                    print(output)


if __name__ == "__main__":
    raise SystemExit(main())
