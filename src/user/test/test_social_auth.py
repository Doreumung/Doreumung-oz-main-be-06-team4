from typing import Any, Dict, Generator
from unittest.mock import AsyncMock

import pytest
import respx
from httpx import Response
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.user.dtos.response import JWTResponse
from src.user.models.models import SocialProvider, User
from src.user.repo.repository import UserRepository
from src.user.services.social_auth import (
    google_callback_handler,
    kakao_callback_handler,
)


@pytest.fixture
def setup_database() -> Generator[Session, None, None]:
    engine = create_engine("postgresql:///:memory:")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    yield db

    db.close()


@pytest.fixture
def mock_user_repo(mocker: Any) -> Any:
    repo = mocker.AsyncMock(UserRepository)
    repo.get_user_by_social_email.return_value = None
    repo.save.return_value = None
    return repo


@pytest.fixture
def mock_kakao_token_response() -> Dict[str, Any]:
    return {
        "access_token": "mock_access_token",
        "token_type": "Bearer",
        "refresh_token": "mock_refresh_token",
        "expires_in": 3600,
    }


@pytest.fixture
def mock_kakao_profile_response() -> Dict[str, Any]:
    return {
        "id": "123456",
        "kakao_account": {"email": "kakao@example.com"},
        "properties": {"nickname": "KakaoUser"},
    }


@pytest.fixture
def mock_google_token_response() -> Dict[str, Any]:
    return {
        "access_token": "mock_access_token",
        "expires_in": 3600,
        "scope": "email profile",
        "token_type": "Bearer",
    }


@pytest.fixture
def mock_google_profile_response() -> Dict[str, Any]:
    return {
        "id": "654321",
        "email": "google@example.com",
        "name": "Google User",
        "given_name": "Google",
        "family_name": "User",
    }


@respx.mock
@pytest.mark.asyncio
async def test_kakao_callback_handler(
    mock_user_repo: AsyncMock,
    mock_kakao_token_response: Dict[str, Any],
    mock_kakao_profile_response: Dict[str, Any],
) -> None:
    token_url = "https://kauth.kakao.com/oauth/token"
    profile_url = "https://kapi.kakao.com/v2/user/me"

    # Kakao Token Request
    respx.post(token_url).mock(return_value=Response(200, json=mock_kakao_token_response))

    # Kakao Profile Request
    respx.get(profile_url).mock(return_value=Response(200, json=mock_kakao_profile_response))

    jwt_response = await kakao_callback_handler(
        token_url=token_url,
        profile_url=profile_url,
        client_id="mock_client_id",
        client_secret="mock_client_secret",
        redirect_uri="http://localhost/callback",
        code="mock_code",
        social_provider=SocialProvider.KAKAO,
        user_repo=mock_user_repo,
    )

    assert isinstance(jwt_response, JWTResponse)
    assert jwt_response.access_token is not None
    assert jwt_response.refresh_token is not None
    mock_user_repo.save.assert_called_once()


@respx.mock
@pytest.mark.asyncio
async def test_google_callback_handler(
    mock_user_repo: AsyncMock,
    mock_google_token_response: Dict[str, Any],
    mock_google_profile_response: Dict[str, Any],
) -> None:
    token_url = "https://oauth2.googleapis.com/token"
    profile_url = "https://www.googleapis.com/oauth2/v2/userinfo"

    # Google Token Request
    respx.post(token_url).mock(return_value=Response(200, json=mock_google_token_response))

    # Google Profile Request
    respx.get(profile_url).mock(return_value=Response(200, json=mock_google_profile_response))

    jwt_response = await google_callback_handler(
        token_url=token_url,
        profile_url=profile_url,
        client_id="mock_client_id",
        client_secret="mock_client_secret",
        redirect_uri="http://localhost/callback",
        code="mock_code",
        social_provider=SocialProvider.GOOGLE,
        user_repo=mock_user_repo,
    )

    assert isinstance(jwt_response, JWTResponse)
    assert jwt_response.access_token is not None
    assert jwt_response.refresh_token is not None
    mock_user_repo.save.assert_called_once()
