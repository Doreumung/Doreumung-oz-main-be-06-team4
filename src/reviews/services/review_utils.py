import shutil
from pathlib import Path
from typing import Any, List, Optional, Set
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from src.reviews.models.models import ImageSourceType, Review, ReviewImage
from src.reviews.repo.review_repo import ReviewRepo

# 업로드 디렉토리 설정
UPLOAD_DIR = Path("uploads")  # 이미지 저장 경로
UPLOAD_DIR.mkdir(exist_ok=True)  # 디렉토리가 없으면 생성


# 유틸리티 함수: 정렬 컬럼 유효성 검증
def validate_order_by(order_by: str, valid_columns: Set[str]) -> Any:
    if order_by not in valid_columns:
        raise HTTPException(status_code=400, detail=f"Invalid order_by value: {order_by}")
    return getattr(Review, order_by)


# 유틸리티 함수: 파일 크기 제한 검증
def validate_file_size(file: UploadFile, max_size_mb: int = 5) -> None:
    """
    파일 크기 검증 함수
    - 파일 크기를 확인하고 최대 크기를 초과하면 예외를 발생시킵니다.
    """
    file.file.seek(0, 2)  # 파일의 끝으로 이동하여 크기를 계산
    file_size = file.file.tell()  # 현재 위치(파일 크기)를 가져옴
    file.file.seek(0)  # 파일의 시작으로 다시 이동

    if file_size > max_size_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum allowed size is {max_size_mb}MB.")


async def handle_file_upload(files: List[UploadFile], review_id: int, review_repo: ReviewRepo) -> None:
    """
    파일 업로드 처리 함수
    - 파일을 디스크에 저장하고 ReviewImage 테이블에 추가
    """
    for file in files:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename cannot be None")

        validate_file_size(file)  # 파일 크기 제한 확인

        # 고유 파일 이름 생성
        unique_filename = f"{uuid4()}_{file.filename}"
        file_path = UPLOAD_DIR / unique_filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 업로드한 파일을 ReviewImage에 저장
        new_image = ReviewImage(
            review_id=review_id,
            filepath=str(file_path),
            source_type="upload",
        )
        await review_repo.save_image(new_image)


async def handle_image_urls(image_urls: List[str], review_id: int, review_repo: ReviewRepo) -> None:
    """
    이미지 URL 처리 함수
    - URL 이미지를 ReviewImage 테이블에 추가
    """
    for image_url in image_urls:
        if image_url:  # 이미지 URL이 None이 아닌 경우
            new_image = ReviewImage(
                review_id=review_id,
                filepath=image_url,
                source_type="LINK",  # 적절한 source_type 값 설정
            )
            await review_repo.save_image(new_image)


def validate_review_image(filepath: Optional[str], source_type: Optional[ImageSourceType]) -> None:
    if filepath is None and source_type is None:
        # 둘 다 비어 있는 경우 허용 (이미지 없이 리뷰 작성)
        return
    if filepath is None or source_type is None:
        # 하나만 비어 있는 경우 예외 발생
        raise ValueError("Both 'filepath' and 'source_type' must be provided together.")


async def save_review_image(
    review_id: int,
    filepath: Optional[str],
    source_type: Optional[ImageSourceType],
    review_repo: ReviewRepo,
) -> Optional[ReviewImage]:
    # 유효성 검사
    validate_review_image(filepath, source_type)

    # 유효한 경우에만 저장
    new_image = ReviewImage(
        review_id=review_id,
        filepath=filepath,
        source_type=source_type,
    )
    saved_image = await review_repo.save_image(new_image)

    return saved_image
