from pydantic import BaseModel, Field, EmailStr


class SignUpRequestBody(BaseModel):
    email: str = Field(..., max_length=10)
    password: str


class UserPasswordRequestBody(BaseModel):
    new_password: str

class UserLoginRequestBody(BaseModel):
    email: EmailStr
    password: str