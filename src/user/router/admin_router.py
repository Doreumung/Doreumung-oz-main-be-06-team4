from fastapi import APIRouter, Depends, HTTPException, status

from src.user.dtos.request import CreateUserRequestBody
from src.user.dtos.response import UserResponse
from src.user.models.models import User
from src.user.repo.repository import UserRepository
from src.user.services.authentication import hash_password

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


@router.post("/superuser", response_model=UserResponse)
async def create_superuser(
    body: CreateUserRequestBody,
    user_repo: UserRepository = Depends(),
) -> UserResponse:
    if await user_repo.get_user_by_email(email=body.email):  # 비동기 호출
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")

    hashed_password = hash_password(plain_text=body.password)
    superuser = User(
        email=body.email,
        password=hashed_password,
        nickname=body.nickname,
        is_superuser=True,
    )
    await user_repo.save(user=superuser)  # 비동기 호출
    return UserResponse.model_validate(superuser)
