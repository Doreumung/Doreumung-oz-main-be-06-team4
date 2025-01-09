import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Set
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from src.reviews.dtos.response import ReviewImageResponse
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
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size is {max_size_mb}MB.",
        )


# 유틸리티 함수: 파일 업로드 처리
async def handle_file_upload(files: List[UploadFile], review_id: int, review_repo: ReviewRepo) -> None:
    """
    파일 업로드 처리 함수
    - 파일을 디스크에 저장하고 ReviewImage 테이블에 추가
    """
    for file in files:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename cannot be None")

        # 파일 크기 검증
        validate_file_size(file)

        # 고유 파일 이름 생성
        unique_filename = f"{uuid4()}_{file.filename}"
        file_path = UPLOAD_DIR / unique_filename

        # 파일 저장
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 업로드한 파일을 ReviewImage에 저장
        new_image = ReviewImage(
            review_id=review_id,
            filepath=str(file_path),
            source_type="file",
        )
        await review_repo.save_image(new_image)


VALID_SOURCE_TYPES = {"url", "file"}


async def handle_image_urls(image_urls: List[str], review_id: int, review_repo: ReviewRepo) -> None:
    """
    이미지 URL 처리 함수
    - URL 이미지를 ReviewImage 테이블에 추가
    """
    for image_url in image_urls:
        if image_url:  # 이미지 URL이 None이 아닌 경우
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


# 유틸리티 함수: 리뷰 이미지 저장
async def save_review_image(
    review_id: int,
    filepath: Optional[str],
    source_type: Optional[str],
    review_repo: ReviewRepo,
) -> Optional[ReviewImage]:
    """
    리뷰 이미지 저장
    - 유효성 검증 후 DB에 저장
    """
    # 유효성 검사
    validate_review_image(filepath, source_type)

    # 유효한 경우에만 저장
    new_image = ReviewImage(
        review_id=review_id,
        filepath=filepath,
        source_type=source_type,
    )
    return await review_repo.save_image(new_image)


async def process_uploaded_files(
    files: Optional[List[UploadFile]],
    review_id: int,
    review_repo: ReviewRepo,
) -> List[ReviewImageResponse]:
    if not files:
        return []

    image_responses = []
    valid_files = []

    for file in files:
        if isinstance(file, UploadFile):
            valid_files.append(file)
        elif isinstance(file, str) and file == "":
            continue  # 빈 문자열 무시
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Expected UploadFile or empty value.",
            )

    for file in valid_files:
        saved_path = f"/uploads/{datetime.now().isoformat()}-{file.filename}"
        try:
            with open(saved_path, "wb") as buffer:
                buffer.write(await file.read())
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file: {file.filename}. Error: {str(e)}",
            )

        new_file_image = await review_repo.save_image(
            ReviewImage(
                review_id=review_id,
                filepath=saved_path,
                source_type="file",
            )
        )
        if new_file_image:
            image_responses.append(
                ReviewImageResponse(
                    id=new_file_image.id,
                    review_id=review_id,
                    filepath=new_file_image.filepath,
                    source_type=new_file_image.source_type,
                )
            )

    return image_responses
