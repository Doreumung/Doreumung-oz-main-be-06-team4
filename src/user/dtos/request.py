from pydantic import BaseModel, EmailStr, Field


class SignUpRequestBody(BaseModel):
    email: str = Field(..., max_length=30)
    password: str


class UserPasswordRequestBody(BaseModel):
    new_password: str


class UserLoginRequestBody(BaseModel):
    email: EmailStr
    password: str


class CreateUserRequestBody(BaseModel):
    email: str = Field(..., max_length=30, examples=["admin@example.com"])
    password: str = Field(..., min_length=8, examples=["securepassword123"])
    username: str = Field(..., min_length=3, max_length=30, examples=["adminuser"])
