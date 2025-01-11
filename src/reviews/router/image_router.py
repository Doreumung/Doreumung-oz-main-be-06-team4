import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, List, Optional

import requests  # type: ignore
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlmodel import select

from src.reviews.dtos.response import ReviewImageResponse, UploadImageResponse
from src.reviews.models.models import ImageSourceType, Review, ReviewImage
from src.reviews.repo.review_repo import ReviewRepo
from src.reviews.services.image_utils import (
    validate_file_extension,
    validate_file_size,
    validate_review_image,
    validate_url_size,
)
from src.user.repo.repository import UserRepository
from src.user.services.authentication import authenticate

image_router = APIRouter(prefix="/images", tags=["Images"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)  # Ensure the upload directory exists


@image_router.post("/upload", response_model=UploadImageResponse)
async def upload_images(
    review_id: int,
    file: Optional[UploadFile] = None,
    url: Optional[str] = None,
    user_id: str = Depends(authenticate),
    image_repo: ReviewRepo = Depends(),
    user_repo: UserRepository = Depends(),
) -> UploadImageResponse:
    user = await user_repo.get_user_by_id(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 검증: 리뷰 존재 여부 확인
    query = select(Review).where(Review.id == review_id)
    result = await image_repo.session.execute(query)
    review = result.unique().scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if not file and not url:
        raise HTTPException(status_code=400, detail="No file or URL provided")

    # 업로드 파일 또는 URL 처리
    file_path = None
    source_type = None

    if file:
        # 파일 크기 및 확장자 검증
        if not file.filename:
            raise HTTPException(status_code=400, detail="Invalid file: Filename cannot be None")
        validate_file_extension(file.filename)
        validate_file_size(file)

        unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = UPLOAD_DIR / unique_filename

        try:
            with file_path.open("wb") as buffer:
                buffer.write(await file.read())
            source_type = ImageSourceType.UPLOAD
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")
    elif url:
        # URL 크기 및 확장자 검증
        validate_url_size(url)
        filename = url.split("/")[-1]
        validate_file_extension(filename)

        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = UPLOAD_DIR / unique_filename

        try:
            response = requests.get(url, stream=True)
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to fetch URL content")
            with file_path.open("wb") as buffer:
                buffer.write(response.content)
            source_type = ImageSourceType.LINK
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"URL processing failed: {str(e)}")

    # ReviewImage 객체 생성 및 DB에 저장
    if file_path and source_type:
        uploaded_image = ReviewImage(
            review_id=review_id,
            filepath=str(file_path),
            source_type=source_type.value,
        )
        await image_repo.save_image(uploaded_image)

    else:
        raise HTTPException(status_code=400, detail="Failed to process file or URL")

    # 해당 리뷰의 모든 이미지 조회
    query = select(ReviewImage).where(ReviewImage.review_id == review_id).order_by(ReviewImage.id)  # type: ignore
    result = await image_repo.session.execute(query)
    all_images = result.unique().scalars().all()

    # 응답 생성
    return UploadImageResponse(
        uploaded_image=ReviewImageResponse(
            id=uploaded_image.id,
            review_id=uploaded_image.review_id,
            filepath=uploaded_image.filepath,
            source_type=uploaded_image.source_type,
            created_at=uploaded_image.created_at,
            updated_at=uploaded_image.updated_at,
        ),
        all_images=[
            ReviewImageResponse(
                id=image.id,
                review_id=image.review_id,  # type: ignore
                filepath=image.filepath,  # type: ignore
                source_type=image.source_type,  # type: ignore
                created_at=image.created_at,
                updated_at=image.updated_at,
            )
            for image in all_images
        ],
    )


# 리뷰와 연결된 이미지 조회
@image_router.get("/images/{review_id}", response_model=List[ReviewImageResponse])
async def get_images_by_review(
    review_id: int,
    image_repo: ReviewRepo = Depends(),
) -> List[ReviewImageResponse]:
    # 검증: 리뷰 존재 여부 확인
    query = select(Review).where(Review.id == review_id)
    result = await image_repo.session.execute(query)
    review = result.unique().scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    # 리뷰와 연관된 이미지 조회
    query = select(ReviewImage).where(ReviewImage.review_id == review_id)  # type: ignore
    result = await image_repo.session.execute(query)
    images = result.unique().scalars().all()

    return [
        ReviewImageResponse(
            id=image.id,
            review_id=image.review_id,  # type: ignore
            filepath=image.filepath,  # type: ignore
            source_type=image.source_type,  # type: ignore
            created_at=image.created_at,
            updated_at=image.updated_at,
        )
        for image in images
    ]


# 특정 이미지 상세조회
@image_router.get("/image/{image_id}", response_model=ReviewImageResponse)
async def get_image_by_id(
    image_id: int,
    image_repo: ReviewRepo = Depends(),
) -> ReviewImageResponse:
    # 검증: 이미지 존재 여부 확인
    query = select(ReviewImage).where(ReviewImage.id == image_id)
    result = await image_repo.session.execute(query)
    image = result.unique().scalar_one_or_none()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    return ReviewImageResponse(
        id=image.id,
        review_id=image.review_id,
        filepath=image.filepath,
        source_type=image.source_type,
        created_at=image.created_at,
        updated_at=image.updated_at,
    )


@image_router.patch("/update", response_model=UploadImageResponse)
async def update_images(
    image_id: int,
    file: Optional[UploadFile] = None,
    url: Optional[str] = None,
    user_id: str = Depends(authenticate),
    image_repo: ReviewRepo = Depends(),
    user_repo: UserRepository = Depends(),
) -> UploadImageResponse:
    user = await user_repo.get_user_by_id(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 검증: 이미지 존재 여부 확인
    query = select(ReviewImage).where(ReviewImage.id == image_id)
    result = await image_repo.session.execute(query)
    existing_image = result.scalar_one_or_none()
    if not existing_image:
        raise HTTPException(status_code=404, detail="Image not found")

    # 기존 파일 삭제 (파일 경로가 존재할 경우)
    if existing_image.source_type == ImageSourceType.UPLOAD.value:
        existing_file_path = Path(existing_image.filepath)
        if existing_file_path.exists():
            existing_file_path.unlink()

    # 새로운 파일 또는 URL 처리
    file_path = None
    source_type = None

    if file:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Invalid file: Filename cannot be None")
        validate_file_extension(file.filename)
        validate_file_size(file)

        unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = UPLOAD_DIR / unique_filename

        try:
            with file_path.open("wb") as buffer:
                buffer.write(await file.read())
            source_type = ImageSourceType.UPLOAD
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")
    elif url:
        validate_url_size(url)
        filename = url.split("/")[-1]
        validate_file_extension(filename)

        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = UPLOAD_DIR / unique_filename

        try:
            response = requests.get(url, stream=True)
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to fetch URL content")
            with file_path.open("wb") as buffer:
                buffer.write(response.content)
            source_type = ImageSourceType.LINK
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"URL processing failed: {str(e)}")

    KST = timezone(timedelta(hours=9))

    # 업데이트된 데이터 저장
    if file_path and source_type:
        existing_image.filepath = str(file_path)
        existing_image.source_type = source_type
        existing_image.updated_at = datetime.now(KST)
        await image_repo.session.commit()
        await image_repo.session.refresh(existing_image)
    else:
        raise HTTPException(status_code=400, detail="Failed to process file or URL")

    return UploadImageResponse(
        uploaded_image=ReviewImageResponse(
            id=existing_image.id,
            review_id=existing_image.review_id,
            filepath=existing_image.filepath,
            source_type=existing_image.source_type,
            created_at=existing_image.created_at,
            updated_at=existing_image.updated_at,
        ),
        all_images=[],  # 업데이트 후 다른 이미지는 반환하지 않음
    )


# 이미지 삭제 엔드포인트
@image_router.delete("/delete", response_model=dict)
async def delete_images(
    image_id: int,
    user_id: str = Depends(authenticate),
    image_repo: ReviewRepo = Depends(),
    user_repo: UserRepository = Depends(),
) -> dict[str, Any]:
    user = await user_repo.get_user_by_id(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 검증: 이미지 존재 여부 확인
    query = select(ReviewImage).where(ReviewImage.id == image_id)
    result = await image_repo.session.execute(query)
    image = result.scalar_one_or_none()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # 업로드된 파일인 경우, 로컬 파일 삭제
    if image.source_type == ImageSourceType.UPLOAD.value:
        file_path = Path(image.filepath)
        if file_path.exists():
            file_path.unlink()

    # 데이터베이스에서 이미지 삭제
    await image_repo.session.delete(image)
    await image_repo.session.commit()

    return {"message": "Image deleted successfully"}
