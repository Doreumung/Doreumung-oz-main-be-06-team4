from fastapi import Depends
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.config.database.connection_async import get_async_session
from src.user.models.models import SocialProvider, User


class UserRepository:
    def __init__(self, session: AsyncSession = Depends(get_async_session)):
        self.session = session

    async def save(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        return user  # 비동기 commit

    async def get_user_by_id(self, user_id: str) -> User | None:
        result = await self.session.execute(select(User).filter_by(id=user_id))
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: EmailStr) -> User | None:
        result = await self.session.execute(select(User).filter_by(email=email))
        return result.scalar_one_or_none()

    async def get_user_by_social_email(self, social_provider: SocialProvider, email: EmailStr) -> User | None:
        result = await self.session.execute(
            select(User).filter(User.social_provider == social_provider, User.email == email)  # type: ignore
        )
        return result.scalar_one_or_none()

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
        await self.session.commit()
