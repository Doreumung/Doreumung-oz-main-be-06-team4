import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

import requests  # type: ignore
from fastapi import HTTPException, UploadFile

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


# 유틸리티 함수: 리뷰 이미지 저장 유효성 검증
def validate_review_image(filepath: Optional[str], source_type: Optional[str]) -> None:
    """
    리뷰 이미지 저장 시 유효성 검사
    - 파일 경로와 소스 타입이 함께 제공되지 않으면 예외를 발생시킵니다.
    """
    if filepath is None and source_type is None:
        return  # 둘 다 비어 있는 경우 허용 (이미지 없이 리뷰 작성)
    if filepath is None or source_type is None:
        raise ValueError("Both 'filepath' and 'source_type' must be provided together.")
