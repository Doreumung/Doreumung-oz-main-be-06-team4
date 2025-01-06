from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr
from sqlmodel import Field

from src.user.models.models import Gender

# 내 정보 조회


class UserInfoResponse(BaseModel):
    id: str
    email: EmailStr
    nickname: str | None = None
    gender: Gender | None = None
    birthday: date | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class UserMeResponse(BaseModel):
    email: EmailStr
    password: str
    nickname: str
    gender: Optional[Gender] = None
    birthday: date

    model_config = ConfigDict(from_attributes=True)


# 다른 사람의 정보 조회


class UserResponse(BaseModel):
    email: EmailStr
    is_superuser: bool

    model_config = ConfigDict(from_attributes=True)


class JWTResponse(BaseModel):
    access_token: str
    refresh_token: str
