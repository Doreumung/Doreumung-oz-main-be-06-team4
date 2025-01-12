import httpx
from fastapi import HTTPException, status

from src.user.dtos.response import JWTResponse
from src.user.models.models import SocialProvider, User
from src.user.repo.repository import UserRepository
from src.user.services.authentication import encode_access_token, encode_refresh_token


async def kakao_callback_handler(
    token_url: str,
    profile_url: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    code: str,
    social_provider: SocialProvider,
    user_repo: UserRepository,
) -> JWTResponse:
    async with httpx.AsyncClient() as client:
        # Access Token 요청
        try:
            token_response = await client.post(
                token_url,
                data={
                    "grant_type": "authorization_code",
                    "client_id": client_id,
                    "redirect_uri": redirect_uri,
                    "code": code,
                    "client_secret": client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            token_response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Kakao token fetch failed: {e.response.json()}",
            )

        token_data = token_response.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Kakao did not return an access token.",
            )

        # 사용자 프로필 요청
        try:
            profile_response = await client.get(
                profile_url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            profile_response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Kakao profile fetch failed: {e.response.json()}",
            )

        user_profile = profile_response.json()
        user_id = str(user_profile.get("id"))
        email = user_profile.get("kakao_account", {}).get("email")
        nickname = user_profile.get("properties", {}).get("nickname")
        if not nickname:
            nickname = email[: email.index("@")]
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not provided by Kakao.",
            )

        # 사용자 확인 및 생성
        user = await user_repo.get_user_by_social_email(
            social_provider=social_provider,
            email=email,
        )
        if user:
            # 기존 사용자
            return JWTResponse(
                access_token=encode_access_token(user_id=user.id), refresh_token=encode_refresh_token(user_id=user.id)
            )

        # 신규 사용자 생성
        user = User.social_signup(
            social_provider=social_provider,
            subject=user_id,
            email=email,
            nickname=nickname,
        )
        await user_repo.save(user=user)
        return JWTResponse(
            access_token=encode_access_token(user_id=user.id), refresh_token=encode_refresh_token(user_id=user.id)
        )


async def google_callback_handler(
    token_url: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    profile_url: str,
    code: str,
    social_provider: SocialProvider,
    user_repo: UserRepository,
) -> JWTResponse:
    async with httpx.AsyncClient() as client:
        # Access Token 요청 디버깅
        try:
            token_response = await client.post(
                token_url,
                data={
                    "grant_type": "authorization_code",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "code": code,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            print("Token Request Data:", token_response.request.content.decode())
            print("Token Response Status:", token_response.status_code)
            print("Token Response Body:", token_response.json())
            token_response.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(f"Google Token Error: {e.response.status_code}, {e.response.json()}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Google token fetch failed: {e.response.json()}",
            )

        # Access Token 추출
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google did not return an access token.",
            )

        # 사용자 프로필 요청
        try:
            profile_response = await client.get(
                profile_url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            profile_response.raise_for_status()
            print("Profile Response:", profile_response.json())
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Google profile fetch failed: {e.response.json()}",
            )

        # 사용자 정보 확인 및 저장
        user_profile = profile_response.json()
        email = user_profile.get("email")
        nickname = user_profile.get("name")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not provided by Google.",
            )

        if not nickname:
            nickname = user_profile.get("given_name", "") + " " + user_profile.get("family_name", "")
            if not nickname.strip():
                nickname = f"user_{user_profile.get('id')}"  # ID 기반 기본값

        # 기존 사용자 확인
        user = await user_repo.get_user_by_social_email(
            social_provider=social_provider,
            email=email,
        )
        if user:
            return JWTResponse(
                access_token=encode_access_token(user_id=user.id), refresh_token=encode_refresh_token(user_id=user.id)
            )

        # 신규 사용자 생성
        user = User.social_signup(
            social_provider=social_provider,
            subject=user_profile["id"],
            email=email,
            nickname=nickname,
        )
        await user_repo.save(user=user)
        return JWTResponse(
            access_token=encode_access_token(user_id=user.id), refresh_token=encode_refresh_token(user_id=user.id)
        )
