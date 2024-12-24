import os
import re
from datetime import datetime, timedelta, timezone
from typing import TypedDict

import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


# 비밀 번호 처리
def hash_password(plain_text: str) -> str:
    hash_password_bytes: bytes = bcrypt.hashpw(plain_text.encode("utf-8"), bcrypt.gensalt())
    return hash_password_bytes.decode("utf-8")


def check_password(plain_text: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_text.encode("utf-8"), hashed_password.encode("utf-8"))


def is_bcrypt_pattern(password: str) -> bool:
    bcrypt_pattern = r"^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$"
    return re.fullmatch(bcrypt_pattern, password) is not None


load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
UTC = timezone.utc

class JWTPayload(TypedDict):
    user_id: int
    exp: int


def encode_access_token(user_id: int, expires_delta: timedelta = timedelta(days=7)) -> str:
    expire = datetime.now(UTC) + expires_delta
    payload: JWTPayload = {
        "user_id": user_id,
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(dict(payload), SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(access_token: str) -> JWTPayload:
    try:
        return jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# 인증 처리
def authenticate(
    auth_header: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    payload: JWTPayload = decode_access_token(auth_header.credentials)
    return payload["user_id"]
