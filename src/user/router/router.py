import asyncio
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.responses import RedirectResponse

from src.config import settings
from src.config.database.connection_async import get_async_session
from src.user.dtos.request import (
    RefreshTokenRequest,
    SignUpRequestBody,
    UpdateUserRequest,
    UserLoginRequestBody,
    UserLogoutRequestBody,
)
from src.user.dtos.response import JWTResponse, UserInfoResponse, UserMeResponse
from src.user.models.models import SocialProvider, User
from src.user.repo.repository import UserRepository
from src.user.services.authentication import (
    authenticate,
    check_password,
    decode_refresh_token,
    encode_access_token,
    encode_refresh_token,
)
from src.user.services.social_auth import (
    google_callback_handler,
    kakao_callback_handler,
)

router = APIRouter(prefix="/api/v1", tags=["User"])


async def send_welcome_email(email: str) -> None:
    await asyncio.sleep(5)
    print(f"Sending welcome email to {email}")


@router.post(
    "/user/signup",
    response_model=UserMeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def sign_up_handler(
    body: SignUpRequestBody,
    user_repo: UserRepository = Depends(),
) -> UserMeResponse:
    new_user = User.create(
        email=body.email,
        password=body.password,
        nickname=body.nickname,
        gender=body.gender,
        birthday=body.birthday,
    )
    await user_repo.save(user=new_user)  # save를 비동기 처리
    return UserMeResponse.model_validate(obj=new_user)


@router.post(
    "/user/login",
    response_model=JWTResponse,
    status_code=status.HTTP_200_OK,
)
async def login_handler(
    body: UserLoginRequestBody,
    user_repo: UserRepository = Depends(),
) -> JWTResponse:
    user = await user_repo.get_user_by_email(email=body.email)  # get도 비동기 처리
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
    return JWTResponse(
        access_token=encode_access_token(user_id=user.id), refresh_token=encode_refresh_token(user_id=user.id)
    )


@router.post(
    "/user/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def logout_handler(
    body: UserLogoutRequestBody,
) -> None:
    try:
        access_payload = decode_refresh_token(body.access_token)
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )
    try:
        refresh_payload = decode_refresh_token(body.refresh_token)
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    if access_payload["user_id"] != refresh_payload["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token mismatch between access and refresh tokens",
        )
    return


# 내 정보 조회
@router.get("/user/me", response_model=UserInfoResponse)
async def get_me_handler(
    user_id: str = Depends(authenticate),
    user_repo: UserRepository = Depends(),
) -> UserInfoResponse:
    user = await user_repo.get_user_by_id(user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    birthday = user.birthday if isinstance(user.birthday, date) else None
    created_at = user.created_at if isinstance(user.created_at, datetime) else None
    updated_at = user.updated_at if isinstance(user.updated_at, datetime) else None

    if created_at:
        created_at = created_at.astimezone(timezone(timedelta(hours=9)))
    if updated_at:
        updated_at = updated_at.astimezone(timezone(timedelta(hours=9)))

    return UserInfoResponse(
        id=user.id,
        email=user.email,
        nickname=user.nickname,
        gender=user.gender,
        birthday=birthday,
        created_at=created_at,
        updated_at=updated_at,
    )


@router.patch("/user/me", response_model=UserMeResponse, status_code=status.HTTP_200_OK)
async def update_user_handler(
    user_id: str = Depends(authenticate),
    update_data: UpdateUserRequest = Body(...),
    user_repo: UserRepository = Depends(),
) -> UserMeResponse:
    user = await user_repo.get_user_by_id(user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if update_data.new_password:
        user.update_password(password=update_data.new_password)
    if update_data.new_nickname:
        user.nickname = update_data.new_nickname
    if update_data.new_birthday:
        # 'user.birthday'에 'date' 객체를 직접 할당하지 않고, 올바르게 변환
        parsed_birthday = date.fromisoformat(str(update_data.new_birthday))
        user.birthday = parsed_birthday

    await user_repo.save(user=user)
    return UserMeResponse.model_validate(obj=user)


@router.delete("/user/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_handler(
    user_id: str = Depends(authenticate),
    user_repo: UserRepository = Depends(),
) -> None:
    user = await user_repo.get_user_by_id(user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already scheduled for deletion",
        )

    user.is_deleted = True
    user.deleted_at = datetime.now(timezone(timedelta(hours=9))) + timedelta(days=3)
    await user_repo.save(user=user)
    return


@router.post(
    "/refresh",
    response_model=JWTResponse,
    status_code=status.HTTP_200_OK,
)
async def refresh_access_token_handler(
    body: RefreshTokenRequest,
) -> JWTResponse:
    try:
        payload = decode_refresh_token(body.refresh_token)
        print(f"Decoded refresh token: {payload}")

        new_access_token = encode_access_token(user_id=str(payload["user_id"]))
        return JWTResponse(access_token=new_access_token, refresh_token=body.refresh_token)

    except HTTPException as e:
        print(f"Refresh token decoding failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )


# 카카오 로그인 api
@router.get(
    "/social/kakao/login",
    status_code=status.HTTP_200_OK,
)
async def kakao_social_login_handler() -> RedirectResponse:
    return RedirectResponse(
        f"https://kauth.kakao.com/oauth/authorize?"
        f"client_id={settings.KAKAO_REST_API_KEY}"
        f"&redirect_uri={settings.KAKAO_REDIRECT_URL}"
        f"&response_type=code"
        f"&scope=account_email",
    )


# 카카오 callback api
@router.get(
    "/social/kakao/callback",
    status_code=status.HTTP_200_OK,
)
async def kakao_social_callback_handler(
    code: str,
    user_repo: UserRepository = Depends(),
) -> JWTResponse:
    return await kakao_callback_handler(
        token_url="https://kauth.kakao.com/oauth/token",
        profile_url="https://kapi.kakao.com/v2/user/me",
        client_id=settings.KAKAO_REST_API_KEY,
        client_secret="",
        redirect_uri=settings.KAKAO_REDIRECT_URL,
        code=code,
        social_provider=SocialProvider.KAKAO,
        user_repo=user_repo,
    )


# 구글 로그인 api
@router.get(
    "/social/google/login",
    status_code=status.HTTP_200_OK,
)
async def google_login_handler() -> RedirectResponse:
    redirect_uri = settings.GOOGLE_REDIRECT_URL  # 확인
    print(f"Redirect URI being sent: {redirect_uri}")
    return RedirectResponse(
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={settings.GOOGLE_REDIRECT_URL}"
        f"&response_type=code"
        f"&scope=openid email profile https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile"
    )


@router.get(
    "/social/google/callback",
    status_code=status.HTTP_200_OK,
)
async def google_social_callback_handler(
    code: str,
    user_repo: UserRepository = Depends(),
) -> JWTResponse:
    # 디버깅용 로그 추가
    print("Google Login Debugging:")
    print(f"Client ID: {settings.GOOGLE_CLIENT_ID}")
    print(f"Client Secret: {settings.GOOGLE_CLIENT_SECRET}")
    print(f"Redirect URI: {settings.GOOGLE_REDIRECT_URL}")
    print(f"Code: {code}")

    return await google_callback_handler(
        token_url="https://oauth2.googleapis.com/token",
        profile_url="https://www.googleapis.com/oauth2/v2/userinfo",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        redirect_uri=settings.GOOGLE_REDIRECT_URL,
        code=code,
        social_provider=SocialProvider.GOOGLE,
        user_repo=user_repo,
    )
