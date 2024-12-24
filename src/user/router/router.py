import asyncio

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasicCredentials, HTTPBearer

from src.config import settings
from src.user.dtos.request import SignUpRequestBody, UserLoginRequestBody
from src.user.dtos.response import JWTResponse, UserMeResponse
from src.user.models.models import SocialProvider, User
from src.user.repo.repository import UserRepository
from src.user.services.authentication import check_password, encode_access_token

router = APIRouter(prefix="/api/v1", tags=["User"])


async def send_welcome_email(email):
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
):
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
):
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
def kakao_social_login_handler():
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
):
    responses = httpx.post(
        "https://kauth.kakao.com/oauth/token",
        data={
            "grant_type": "authorization_code",
            "client_id": settings.kakao_rest_api_key,
            "redirect_uri": settings.kakao_redirect_url,
            "code": code,
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        },
    )

    responses.raise_for_status()
    if responses.is_success:
        access_token: str = responses.json().get["access_token"]
        profile_response = httpx.get(
            "https://kauth.kakao.com/oauth/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        profile_response.raise_for_status()
        if profile_response.is_success:
            user_profile: dict = profile_response.json()
            user_subject: str = user_profile["id"]
            email: str = profile_response.json()["kakao_account"]["email"]
            user: User | None = user_repo.get_user_by_social_email(social_provider=SocialProvider.KAKAO, email=email)

            if user:
                return JWTResponse(access_token=encode_access_token(user_id=user.id))
            user = User.social_signup(
                social_provider=SocialProvider.KAKAO,
                subject=user_subject,
                email=email,
            )
            assert user is not None
            user_repo.save(user=user)
            return JWTResponse(access_token=encode_access_token(user_id=user.id))
        return profile_response.json()
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="kakao social callback failed",
    )
