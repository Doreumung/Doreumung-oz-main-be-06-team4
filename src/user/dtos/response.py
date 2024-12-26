from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr

from src.user.models.models import Gender

# 내 정보 조회


class UserInfoResponse(BaseModel):
    id: int
    email: EmailStr
    username: str
    nickname: Optional[str] = None
    phone_number: Optional[str] = None
    gender: Optional[Gender] = None
    birthday: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserMeResponse(BaseModel):
    email: EmailStr
    password: str
    username: str
    nickname: str
    phone_number: str
    gender: Gender
    birthday: date

    model_config = ConfigDict(from_attributes=True)


# 다른 사람의 정보 조회


class UserResponse(BaseModel):
    email: EmailStr
    username: str
    is_superuser: bool

    class Config:
        from_attributes = True  # ORM 객체에서 모델 생성 가능


class JWTResponse(BaseModel):
    access_token: str
    refresh_token: str
