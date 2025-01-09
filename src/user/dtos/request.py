from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from src.user.models.models import Gender


class SignUpRequestBody(BaseModel):
    email: EmailStr
    password: str
    nickname: str = Field(..., max_length=30)
    gender: Optional[Gender] = None
    birthday: date


class UpdateUserRequest(BaseModel):
    new_password: Optional[str] = None
    new_nickname: Optional[str] = None
    new_birthday: Optional[date] = None
    new_gender: Optional[Gender | Literal["none"]] = None


class UserLoginRequestBody(BaseModel):
    email: EmailStr
    password: str


class UserLogoutRequestBody(BaseModel):
    access_token: str
    refresh_token: str


class CreateUserRequestBody(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, examples=["securepassword123"])
    nickname: str = Field(..., max_length=30, examples=["string"])


class RefreshTokenRequest(BaseModel):
    refresh_token: str
