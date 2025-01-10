from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator, Generator, Optional

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src import Review  # type: ignore
from src.travel.models.travel_route_place import TravelRoute
from src.user.models.models import User


@pytest_asyncio.fixture(scope="function")
async def setup_data(async_session: AsyncSession) -> Optional[User]:
    user = User(
        id="1",
        email="test@example.com",
        password="test",
        nickname="test",
        updated_at=datetime.now(),
        created_at=datetime.now(),
    )
    async_session.add(user)
    await async_session.commit()

    return await async_session.get(User, "1")


@pytest_asyncio.fixture(scope="function")
async def setup_travelroute(async_session: AsyncSession, setup_data: User) -> Optional[TravelRoute]:
    route = TravelRoute(
        id=1,
        title="dadw",
        user_id="1",
        regions="제주시",
        themes="자연",
        breakfast=True,
        morning=1,
        lunch=True,
        afternoon=1,
        dinner=True,
    )
    async_session.add(route)
    await async_session.commit()
    return await async_session.get(TravelRoute, 1)


@pytest_asyncio.fixture(scope="function")
async def setup_review(
    async_session: AsyncSession, setup_data: User, setup_travelroute: TravelRoute
) -> Optional[Review]:
    user = setup_data
    travel_route = setup_travelroute
    review = Review(
        id=1,
        user_id=user.id,
        travel_route_id=travel_route.id,
        title="Test review",
        rating=4.0,
        content="Test content",
    )
    async_session.add(review)
    await async_session.commit()
    return await async_session.get(Review, 1)


KST = timezone(timedelta(hours=9))
