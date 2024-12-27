import os
import re
import time
from datetime import datetime, timedelta, timezone
from typing import TypedDict

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
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
    user_id: int
    exp: int


def encode_access_token(user_id: int, expires_delta: timedelta = timedelta(days=7)) -> str:
    expire = datetime.now(KST) + expires_delta
    payload: JWTPayload = {
        "user_id": user_id,
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(dict(payload), SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(access_token: str) -> JWTPayload:
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        return JWTPayload(user_id=payload["user_id"], exp=payload["exp"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def encode_refresh_token(user_id: int, expires_delta: timedelta = timedelta(days=7)) -> str:
    expire = datetime.now(KST) + expires_delta
    payload = {
        "user_id": user_id,
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(dict(payload), SECRET_KEY, algorithm=ALGORITHM)


def decode_refresh_token(token: str) -> JWTPayload:
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Ensure the decoded token matches the JWTPayload structure
        payload: JWTPayload = {
            "user_id": int(decoded_token["user_id"]),
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
) -> int:
    payload: JWTPayload = decode_access_token(access_token=auth_header.credentials)

    # token 만료 검사
    EXPIRY_SECONDS = 60 * 60 * 24 * 7
    if payload["exp"] + EXPIRY_SECONDS < time.time():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )

    return payload["user_id"]
