import asyncio
import time
from datetime import datetime

import bcrypt
import pytest

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.user.models.models import User
from src.user.repo.repository import UserRepository
from src.user.services.authentication import (
    check_password,
    decode_refresh_token,
    encode_access_token,
    encode_refresh_token,
)





# # 회원가입
# @pytest.mark.asyncio
# async def test_sign_up_service(async_session: AsyncSession) -> None:
#     # 회원가입 데이터
#     signup_data = {
#         "email": "test@example.com",
#         "password": "password123",
#         "nickname": "tester",
#         "gender": "male",
#         "birthday": "1990-01-01",
#     }
#
#     # UserRepository를 사용하여 사용자 생성
#     user_repo = UserRepository(async_session)
#     hashed_password = bcrypt.hashpw(signup_data["password"].encode(), bcrypt.gensalt()).decode()
#     new_user = User(
#         email=signup_data["email"],
#         password=hashed_password,
#         nickname=signup_data["nickname"],
#         gender=signup_data["gender"],
#         birthday=datetime.strptime(signup_data["birthday"], "%Y-%m-%d").date(),
#     )
#     await user_repo.save(user=new_user)
#
#     # 데이터베이스에서 확인
#     result = await async_session.execute(select(User).where(User.email == signup_data["email"]))  # type: ignore
#     user = result.unique().scalar_one_or_none()
#
#     # 검증
#     assert user is not None
#     assert user.email == signup_data["email"]
#     assert bcrypt.checkpw(signup_data["password"].encode(), user.password.encode())
#
# 회원가입
@pytest.mark.asyncio
async def test_sign_up(async_session: AsyncSession, client:AsyncClient) -> None:
    # 회원가입 데이터
    signup_data = {
        "email": "test@example.com",
        "password": "password123",
        "nickname": "tester",
        "gender": "male",
        "birthday": "1990-01-01",
    }
    response = await client.post("/api/v1/user/signup", json=signup_data)

    assert response.status_code == 201
    assert response.json()["email"] == signup_data["email"]
    # DB에서 확인
    db_user = await async_session.execute(select(User).where(User.email == signup_data["email"]))  # type: ignore
    user = db_user.unique().scalar_one_or_none()
    assert user is not None
    assert user.email == signup_data["email"]


# 로그인
@pytest.mark.asyncio
async def test_login_without_http_request(async_session: AsyncSession, client:AsyncClient) -> None:
    # 사용자 생성
    hashed_password = bcrypt.hashpw("password".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = User(
        id="1",
        email="test@example.com",
        password=hashed_password,
        nickname="tester",
        gender="male",
        birthday=datetime.strptime("1990-01-01", "%Y-%m-%d").date(),
    )
    async_session.add(user)
    await async_session.commit()

    # 로그인 데이터
    login_data = {"email": "test@example.com", "password": "password"}

    # 직접 라우터 함수 호출
    user_repo = UserRepository(async_session)
    user_from_db = await user_repo.get_user_by_email(login_data["email"])

    # 패스워드 확인
    if user_from_db and check_password(login_data["password"], user_from_db.password):
        access_token = encode_access_token(user_id=user_from_db.id)
        refresh_token = encode_refresh_token(user_id=user_from_db.id)

    # 결과 확인
    assert user_from_db is not None
    assert access_token is not None
    assert refresh_token is not None


# 로그아웃
@pytest.mark.asyncio
async def test_logout_handler(async_session: AsyncSession, client: AsyncClient) -> None:
    # 새로운 유저 생성 (DB에 저장)
    # birthday 값을 datetime.date 객체로 변환
    parsed_birthday = datetime.strptime("1990-01-01", "%Y-%m-%d").date()
    user = User(
        id="1",
        email="test@example.com",
        password="hashedpassword",  # 실제로는 hashed password 사용
        nickname="tester",
        gender="male",
        birthday=parsed_birthday,
    )

    async_session.add(user)
    await async_session.commit()

    # refresh_token과 access_token 생성
    refresh_token = encode_refresh_token(user_id=user.id)
    access_token = encode_access_token(user_id=user.id)

    response = await client.post(
        "/api/v1/user/logout",
        json={"access_token": access_token, "refresh_token": refresh_token},
    )
    assert response.status_code == 204

    invalid_access_token = encode_access_token(user_id="2")  # 다른 유저의 access_token
    response = await client.post(
        "/api/v1/user/logout",
        json={"access_token": invalid_access_token, "refresh_token": refresh_token},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Token mismatch between access and refresh tokens"


# 회원 정보 조회
@pytest.mark.asyncio
async def test_get_user_info(async_session: AsyncSession, client:AsyncClient) -> None:

    # 사용자 생성
    hashed_password = bcrypt.hashpw("password123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    parsed_birthday = datetime.strptime("1990-01-01", "%Y-%m-%d").date()
    user = User(
        id="1",
        email="test@example.com",
        password=hashed_password,  # 실제로는 hashed password 사용
        nickname="tester",
        gender="male",
        birthday=parsed_birthday,
    )
    async_session.add(user)
    await async_session.commit()

    # TestClient로 로그인 후 토큰 발급
    login_data = {"email": "test@example.com", "password": "password123"}

    # 사용자 조회 (TestClient 사용 없이 직접 UserRepository를 사용하여 로그인 검증)
    user_repo = UserRepository(async_session)
    user_from_db = await user_repo.get_user_by_email(login_data["email"])

    # 패스워드 검증
    if user_from_db and check_password(login_data["password"], user_from_db.password):
        # 액세스 토큰 생성
        access_token = encode_access_token(user_id=user_from_db.id)

    # 사용자 정보 조회
    # 'access_token'을 직접 사용하여 로그인한 후, 사용자 정보를 가져오는 로직
    assert user_from_db is not None
    assert user_from_db.email == login_data["email"]
    assert user_from_db.nickname == "tester"
    assert access_token is not None


# 회원 정보 업데이트
@pytest.mark.asyncio
async def test_update_user_info(async_session: AsyncSession, client:AsyncClient) -> None:
    # 사용자 생성
    hashed_password = bcrypt.hashpw("password123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    parsed_birthday = datetime.strptime("1990-01-01", "%Y-%m-%d").date()
    user = User(
        id="1",
        email="test@example.com",
        password=hashed_password,  # 실제로는 hashed password 사용
        nickname="tester",
        gender="male",
        birthday=parsed_birthday,
    )
    async_session.add(user)
    await async_session.commit()

    # 사용자 정보 업데이트
    user.nickname = "updated_nickname"
    await async_session.commit()

    # 업데이트된 사용자 정보 확인
    result = await async_session.execute(select(User).filter(User.id == "1"))  # type: ignore
    updated_user = result.unique().scalar_one_or_none()

    assert updated_user is not None
    assert updated_user.nickname == "updated_nickname"


# 계정 삭제
@pytest.mark.asyncio
async def test_delete_user_handler(async_session: AsyncSession, client:AsyncClient) -> None:
    # 유저 생성
    hashed_password = bcrypt.hashpw("password123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    parsed_birthday = datetime.strptime("1990-01-01", "%Y-%m-%d").date()
    user = User(
        id="1",
        email="test@example.com",
        password=hashed_password,
        nickname="tester",
        gender="male",
        birthday=parsed_birthday,
    )
    async_session.add(user)
    await async_session.commit()

    # 유저 삭제
    user.is_deleted = True
    user.deleted_at = datetime.now()
    await async_session.commit()

    # 삭제된 유저 확인
    result = await async_session.execute(select(User).where(User.id == "1"))  # type: ignore
    deleted_user = result.unique().scalar_one_or_none()

    assert deleted_user is not None
    assert deleted_user.is_deleted is True
    assert deleted_user.deleted_at is not None

    # 이미 삭제된 유저가 다시 삭제 시도
    user.is_deleted = True  # 이미 삭제된 상태로 설정
    await async_session.commit()

    result = await async_session.execute(select(User).where(User.id == "1"))  # type: ignore
    re_deleted_user = result.unique().scalar_one_or_none()

    assert re_deleted_user is not None  # 유저가 None이 아니어야 함
    assert re_deleted_user.is_deleted is True  # 유저가 여전히 삭제됨을 확인


# 리프레쉬 토큰
@pytest.mark.asyncio
async def test_refresh_token(async_session: AsyncSession, client: AsyncClient) -> None:
    # 새로운 유저 생성 (DB에 저장)
    hashed_password = bcrypt.hashpw("password123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    parsed_birthday = datetime.strptime("1990-01-01", "%Y-%m-%d").date()
    user = User(
        id="1",
        email="test@example.com",
        password=hashed_password,  # 실제로는 hashed password 사용
        nickname="tester",
        gender="male",
        birthday=parsed_birthday,
    )

    async_session.add(user)
    await async_session.commit()

    # refresh_token 생성
    refresh_token = encode_refresh_token(user_id=user.id)

    # TestClient로 API 요청 보내기
    response = await client.post(
        "/api/v1/refresh",
        json={"refresh_token": refresh_token},
    )

    # 응답 검증
    assert response.status_code == 200
    assert "access_token" in response.json()

    # refresh_token 유효성 검증
    payload = decode_refresh_token(refresh_token)
    assert payload["user_id"] == user.id
