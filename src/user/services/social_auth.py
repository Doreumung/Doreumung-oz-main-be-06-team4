import httpx
from fastapi import HTTPException, status

from src.user.dtos.response import JWTResponse
from src.user.models.models import SocialProvider, User
from src.user.repo.repository import UserRepository
from src.user.services.authentication import encode_access_token


def social_callback_handler(
    token_url: str,
    profile_url: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    code: str,
    social_provider: SocialProvider,
    user_repo: UserRepository,
) -> JWTResponse:
    # Access Token 요청
    responses = httpx.post(
        token_url,
        data={
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "code": code,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
    )
    responses.raise_for_status()

    if responses.is_success:
        access_token: str = responses.json().get("access_token")
        # 사용자 프로필 요청
        profile_response = httpx.get(
            profile_url,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        profile_response.raise_for_status()

        if profile_response.is_success:
            user_profile: dict[str, str] = profile_response.json()
            user_subject: str = user_profile["id"]
            email: str = user_profile.get("email", "")
            if not email:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email not provided")

            # 사용자 확인 및 생성
            user: User | None = user_repo.get_user_by_social_email(
                social_provider=social_provider,
                email=email,
            )
            if user:
                return JWTResponse(access_token=encode_access_token(user_id=user.id))

            user = User.social_signup(
                social_provider=social_provider,
                subject=user_subject,
                email=email,
            )
            assert user is not None
            user_repo.save(user=user)
            return JWTResponse(access_token=encode_access_token(user_id=user.id))

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"{social_provider.value} social callback failed",
    )
