import re
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, TypedDict

import bcrypt
import jwt
from fastapi import Depends, Header, HTTPException, WebSocketException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.config import settings


# 비밀 번호 처리
def hash_password(plain_text: str) -> str:
    hash_password_bytes: bytes = bcrypt.hashpw(plain_text.encode("utf-8"), bcrypt.gensalt())
    return hash_password_bytes.decode("utf-8")


def check_password(plain_text: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_text.encode("utf-8"), hashed_password.encode("utf-8"))


def is_bcrypt_pattern(password: str) -> bool:
    bcrypt_pattern = r"^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$"
    return re.fullmatch(bcrypt_pattern, password) is not None


SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
KST = timezone(timedelta(hours=9))


class JWTPayload(TypedDict):
    user_id: str
    type: str
    exp: int


def encode_access_token(user_id: str, expires_delta: timedelta = timedelta(hours=1)) -> str:
    expire = datetime.now(KST) + expires_delta
    payload: JWTPayload = {
        "user_id": user_id,
        "type": "access",
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(dict(payload), SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(access_token: str) -> JWTPayload:
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        return JWTPayload(user_id=payload["user_id"], type=payload["type"], exp=payload["exp"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def encode_refresh_token(user_id: str, expires_delta: timedelta = timedelta(days=7)) -> str:
    expire = datetime.now(KST) + expires_delta
    payload = {
        "user_id": user_id,
        "type": "refresh",
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(dict(payload), SECRET_KEY, algorithm=ALGORITHM)


def decode_refresh_token(token: str) -> JWTPayload:
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Ensure the decoded token matches the JWTPayload structure
        payload: JWTPayload = {
            "user_id": str(decoded_token["user_id"]),
            "type": str(decoded_token["type"]),
            "exp": int(decoded_token["exp"]),
        }
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# 인증 처리
def authenticate(
    auth_header: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
) -> str:
    payload: JWTPayload = decode_access_token(access_token=auth_header.credentials)

    # token 만료 검사
    EXPIRY_SECONDS = 60 * 60 * 24 * 7
    if payload["exp"] + EXPIRY_SECONDS < time.time():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )

    return payload["user_id"]


def authenticate_optional(
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
) -> Optional[str]:
    if auth_header is None:  # 인증 헤더가 없는 경우
        return None

    try:
        payload: JWTPayload = decode_access_token(access_token=auth_header.credentials)

        # token 만료 검사
        EXPIRY_SECONDS = 60 * 60 * 24 * 7
        if payload["exp"] + EXPIRY_SECONDS < time.time():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
            )

        return payload["user_id"]
    except Exception:
        return None


def websocket_authenticate(access_token: str) -> str:
    payload: JWTPayload = decode_access_token(access_token=access_token)

    # token 만료 검사
    EXPIRY_SECONDS = 60 * 60 * 24 * 7
    if payload["exp"] + EXPIRY_SECONDS < time.time():
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Token expired")

    return payload["user_id"]
