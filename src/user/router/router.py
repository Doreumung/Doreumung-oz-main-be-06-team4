import asyncio

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import RedirectResponse

from src.config import settings
from src.user.dtos.request import SignUpRequestBody, UserLoginRequestBody
from src.user.dtos.response import JWTResponse, UserMeResponse
from src.user.models.models import SocialProvider, User
from src.user.repo.repository import UserRepository
from src.user.services.authentication import check_password, encode_access_token
from src.user.services.social_auth import social_callback_handler

router = APIRouter(prefix="/api/v1", tags=["User"])


async def send_welcome_email(email: str) -> None:
    await asyncio.sleep(5)
    print(f"Sending welcome email to {email}")


@router.post(
    "",
    response_model=UserMeResponse,
    status_code=status.HTTP_201_CREATED,
)
def sign_up_handler(
    body: SignUpRequestBody,
    background_tasks: BackgroundTasks,
    user_repo: UserRepository = Depends(),
) -> UserMeResponse:
    new_user = User.create(email=body.email, password=body.password)
    user_repo.save(user=new_user)
    background_tasks.add_task(send_welcome_email, email=new_user.email)
    return UserMeResponse.model_validate(obj=new_user)


@router.post(
    "/user/login",
    response_model=JWTResponse,
    status_code=status.HTTP_200_OK,
)
def login_handler(
    body: UserLoginRequestBody,
    user_repo: UserRepository = Depends(),
) -> JWTResponse:
    user = user_repo.get_user_by_email(email=body.email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if not check_password(plain_text=body.password, hashed_password=user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    return JWTResponse(access_token=encode_access_token(user_id=user.id))


# 카카오 로그인 api
@router.get(
    "/social/kakao/login",
    status_code=status.HTTP_200_OK,
)
def kakao_social_login_handler() -> RedirectResponse:
    return RedirectResponse(
        "https://kauth.kakao.com/oauth/authorize"
        f"?client_id={settings.kakao_rest_api_key}"
        f"&redirect_uri={settings.kakao_redirect_url}"
        f"&response_type=code",
    )


# 카카오 callback api
@router.get(
    "/social/kakao/callback",
    status_code=status.HTTP_200_OK,
)
def kakao_social_callback_handler(
    code: str,
    user_repo: UserRepository = Depends(),
) -> JWTResponse:
    return social_callback_handler(
        token_url="https://kauth.kakao.com/oauth/token",
        profile_url="https://kapi.kakao.com/v2/user/me",
        client_id=settings.kakao_rest_api_key,
        client_secret="",
        redirect_uri=settings.kakao_redirect_url,
        code=code,
        social_provider=SocialProvider.KAKAO,
        user_repo=user_repo,
    )


# 구글 로그인 api
@router.get(
    "/social/google/login",
    status_code=status.HTTP_200_OK,
)
def google_login_handler() -> RedirectResponse:
    return RedirectResponse(
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"&client_id={settings.google_client_id}"
        f"&redirect_uri={settings.google_redirect_url}"
        f"&response_type=code"
        f"&scope=email profile"
    )


@router.get(
    "/social/google/callback",
    status_code=status.HTTP_200_OK,
)
def google_social_callback_handler(
    code: str,
    user_repo: UserRepository = Depends(),
) -> JWTResponse:
    return social_callback_handler(
        token_url="https://oauth2.googleapis.com/token",
        profile_url="https://www.googleapis.com/oauth2/v2/userinfo",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        redirect_uri=settings.google_redirect_url,
        code=code,
        social_provider=SocialProvider.GOOGLE,
        user_repo=user_repo,
    )
