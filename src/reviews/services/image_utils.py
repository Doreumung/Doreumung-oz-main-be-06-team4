import shutil
import uuid
from datetime import datetime
from os import access
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

import boto3
import requests  # type: ignore
from botocore.exceptions import NoCredentialsError
from fastapi import FastAPI, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.reviews.dtos.response import ReviewImageResponse
from src.reviews.models.models import ImageSourceType, Review, ReviewImage
from src.reviews.repo.review_repo import ReviewRepo

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
# 업로드 디렉토리 설정
UPLOAD_DIR = Path("uploads")  # 이미지 저장 경로
UPLOAD_DIR.mkdir(exist_ok=True)  # 디렉토리가 없으면 생성


# 파일 이름 확장자 검증
def validate_file_extension(filename: str) -> None:
    if "." not in filename or filename.rsplit(".", 1)[1].lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File extension must be one of {ALLOWED_EXTENSIONS}",
        )


# 유틸리티 함수: 파일 크기 제한 검증
def validate_file_size(file: UploadFile, max_size_mb: int = 10) -> None:
    """
    파일 크기 검증 함수
    - 파일 크기를 확인하고 최대 크기를 초과하면 예외를 발생시킵니다.
    """
    file.file.seek(0, 2)  # 파일의 끝으로 이동하여 크기를 계산
    file_size = file.file.tell()  # 현재 위치(파일 크기)를 가져옴
    file.file.seek(0)  # 파일의 시작으로 다시 이동

    if file_size > max_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size is {max_size_mb}MB.",
        )


def validate_url_size(url: str, max_size_mb: int = 10) -> None:
    """
    URL을 통한 이미지 크기 검증 함수.
    - Content-Length 헤더를 사용하여 파일 크기를 검증합니다.
    """
    try:
        response = requests.head(url, allow_redirects=True)
        content_length = response.headers.get("Content-Length")

        if content_length and int(content_length) > max_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail=f"URL file too large. Maximum allowed size is {max_size_mb}MB.",
            )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to validate URL size: {str(e)}",
        )


# 데이터 검증 유틸
def validate_source_type(source_type: str) -> ImageSourceType:

    try:
        return ImageSourceType(source_type)
    except ValueError:
        raise ValueError(f"Invalid source_type: {source_type}. Must be one of {[e.value for e in ImageSourceType]}")


async def handle_image_urls(image_urls: List[str], review_id: int, review_repo: ReviewRepo) -> None:
    """
    이미지 URL 처리 함수
    - URL 이미지를 ReviewImage 테이블에 추가
    """
    existing_urls = await review_repo.get_existing_image_urls(review_id)
    for image_url in image_urls:
        if image_url and image_url not in existing_urls:  # 이미지 URL이 None이 아닌 경우
            source_type = ImageSourceType.LINK  # Enum 사용
            new_image = ReviewImage(
                review_id=review_id,
                filepath=image_url,
                source_type=source_type.value,  # Enum의 값만 사용
            )
            await review_repo.save_image(new_image)


# async def delete_file_from_s3(filepath: str):
AWS_ACCESS_KEY = settings.AWS_ACCESS_KEY
AWS_SECRET_KEY = settings.AWS_SECRET_KEY
AWS_REGION = settings.AWS_REGION
BUCKET_NAME = settings.BUCKET_NAME


s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION,
)


async def handle_file_or_url(file: Optional[UploadFile], url: Optional[str]) -> tuple[str, ImageSourceType]:
    """
    파일 또는 URL을 처리하고, S3에 업로드한 URL을 반환합니다.
    """
    if not file and not url:
        raise HTTPException(status_code=400, detail="No file or URL provided")

    if file:
        # 파일 검증 및 업로드
        if not file.filename:
            raise HTTPException(status_code=400, detail="Invalid file: Filename cannot be None")
        validate_file_extension(file.filename)
        validate_file_size(file)

        unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
        try:
            # S3 업로드
            s3_client.upload_fileobj(file.file, BUCKET_NAME, unique_filename)
            s3_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{unique_filename}"
            return s3_url, ImageSourceType.UPLOAD
        except NoCredentialsError:
            raise HTTPException(status_code=500, detail="AWS credentials not available")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    elif url:
        # URL 검증 및 S3에 저장
        validate_url_size(url)
        filename = url.split("/")[-1]
        validate_file_extension(filename)

        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        try:
            response = requests.get(url, stream=True)
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to fetch URL content")

            # S3 업로드
            s3_client.upload_fileobj(response.raw, BUCKET_NAME, unique_filename)
            s3_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{unique_filename}"
            return s3_url, ImageSourceType.LINK
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"URL processing failed: {str(e)}")

    raise HTTPException(status_code=400, detail="Failed to process file or URL")
