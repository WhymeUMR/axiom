import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def test_create_and_reveal_game() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=create_app()), base_url="http://test"
    ) as client:
        created = await client.post(
            "/api/games",
            json={"width": 9, "height": 9, "mineCount": 10, "seed": 7},
        )
        game_id = created.json()["id"]
        revealed = await client.post(
            f"/api/games/{game_id}/reveal", json={"row": 0, "column": 0}
        )

    assert created.status_code == 201
    assert revealed.status_code == 200
    assert revealed.json()["grid"][0][0]["state"] == "revealed"


async def test_unknown_game_returns_404() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=create_app()), base_url="http://test"
    ) as client:
        response = await client.get("/api/games/missing")

    assert response.status_code == 404


async def test_active_game_does_not_disclose_mines() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=create_app()), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/games",
            json={"width": 9, "height": 9, "mineCount": 10, "seed": 7},
    )

    assert response.status_code == 201
    assert all("mine" not in cell for row in response.json()["grid"] for cell in row)
