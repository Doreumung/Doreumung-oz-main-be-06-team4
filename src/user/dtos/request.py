from datetime import date

from pydantic import BaseModel, EmailStr, Field

from src.user.models.models import Gender


class SignUpRequestBody(BaseModel):
    email: EmailStr
    password: str
    username: str = Field(..., max_length=30)
    nickname: str = Field(..., max_length=30)
    phone_number: str = Field(..., max_length=30)
    gender: Gender
    birthday: date


class UpdateUserRequest(BaseModel):
    new_password: str
    new_nickname: str
    new_birthday: date


class UserLoginRequestBody(BaseModel):
    email: EmailStr
    password: str


class UserLogoutRequestBody(BaseModel):
    access_token: str
    refresh_token: str


class CreateUserRequestBody(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, examples=["securepassword123"])
    username: str = Field(..., min_length=3, max_length=30, examples=["adminuser"])
