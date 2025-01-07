import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.testclient import TestClient

from src import Place, TravelRoute, TravelRoutePlace, User  # type: ignore
from src.config.database.connection_async import get_async_session
from src.main import app
from src.user.services.authentication import authenticate


@pytest_asyncio.fixture
async def client() -> AsyncClient:  # type: ignore
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.mark.asyncio
class TestRouter:
    async def test_generator_travel_route(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/travelroute",
            json={
                "config": {
                    "regions": ["서귀포시", "한림읍"],
                    "themes": ["자연", "액티비티"],
                    "schedule": {"breakfast": True, "morning": 1, "lunch": True, "afternoon": 1, "dinner": True},
                }
            },
        )
        assert response.status_code == 200

    async def test_re_generator_travel_route(
        self, client: AsyncClient, user_save_init: tuple[User, User], place_list_init: list[Place]
    ) -> None:
        async def mock_authenticate() -> str:
            return user_save_init[0].id

        app.dependency_overrides[authenticate] = mock_authenticate
        response = await client.patch(
            "/api/v1/travelroute",
            json={
                "title": "와우 정말 재밌겠는데요?!",
                "schedule": {
                    "morning": [{"place_id": place_list_init[0].id, "name": "string", "latitude": 0, "longitude": 0}],
                    "afternoon": [{"place_id": place_list_init[1].id, "name": "string", "latitude": 0, "longitude": 0}],
                },
                "config": {
                    "regions": ["서귀포시", "한림읍"],
                    "themes": ["자연", "액티비티"],
                    "schedule": {"breakfast": True, "morning": 1, "lunch": True, "afternoon": 1, "dinner": True},
                },
            },
        )
        assert response.status_code == 200

    async def test_save_travel_route(
        self, client: AsyncClient, user_save_init: tuple[User, User], place_list_init: list[Place]
    ) -> None:
        async def mock_authenticate() -> str:
            return user_save_init[0].id

        app.dependency_overrides[authenticate] = mock_authenticate
        response = await client.post(
            url="/api/v1/travelroute/save",
            json={
                "title": "와우 정말 재밌겠는데요?!",
                "schedule": {
                    "breakfast": {"place_id": place_list_init[0].id, "name": "string", "latitude": 0, "longitude": 0},
                    "morning": [{"place_id": place_list_init[1].id, "name": "string", "latitude": 0, "longitude": 0}],
                    "lunch": {"place_id": place_list_init[2].id, "name": "string", "latitude": 0, "longitude": 0},
                    "afternoon": [{"place_id": place_list_init[3].id, "name": "string", "latitude": 0, "longitude": 0}],
                    "dinner": {"place_id": place_list_init[4].id, "name": "string", "latitude": 0, "longitude": 0},
                },
                "config": {
                    "regions": ["제주시"],
                    "themes": ["자연"],
                    "schedule": {"breakfast": True, "morning": 1, "lunch": True, "afternoon": 1, "dinner": True},
                },
            },
        )
        assert response.status_code == 200

    async def test_get_travel_routes(
        self,
        client: AsyncClient,
        user_save_init: tuple[User, User],
        travel_route_init: list[TravelRoute],
        place_list_init: list[Place],
        travel_route_place_init: list[TravelRoutePlace],
    ) -> None:
        async def mock_authenticate() -> str:
            return user_save_init[0].id

        app.dependency_overrides[authenticate] = mock_authenticate
        response = await client.get("/api/v1/travelroute")
        assert response.status_code == 200

    # async def test_get_one_travel_route(
    #     self,
    #     client: AsyncClient,
    #     user_save_init: tuple[User, User],
    #     travel_route_init: list[TravelRoute],
    #     place_list_init: list[Place],
    #     travel_route_place_init: list[TravelRoutePlace],
    # ) -> None:
    #     async def mock_authenticate() -> str:
    #         return user_save_init[0].id
    #
    #     app.dependency_overrides[authenticate] = mock_authenticate
    #     response = await client.get(f"/api/v1/travelroute/{travel_route_init[0].id}")
    #     assert response.status_code == 200

    async def test_delete_one_travel_route(
        self, client: AsyncClient, user_save_init: tuple[User, User], travel_route_init: list[TravelRoute]
    ) -> None:
        async def mock_authenticate() -> str:
            return user_save_init[0].id

        app.dependency_overrides[authenticate] = mock_authenticate
        response = await client.delete(f"/api/v1/travelroute/{travel_route_init[0].id}")
        assert response.status_code == 204
