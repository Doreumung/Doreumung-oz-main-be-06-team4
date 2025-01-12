from pathlib import Path
from typing import Any, Optional

import requests  # type: ignore
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlmodel import select

from src.reviews.dtos.response import ReviewImageResponse, UploadImageResponse
from src.reviews.models.models import ImageSourceType, Review, ReviewImage
from src.reviews.repo.review_repo import ReviewRepo
from src.reviews.services.image_utils import handle_file_or_url
from src.user.repo.repository import UserRepository
from src.user.services.authentication import authenticate

image_router = APIRouter(prefix="/images", tags=["Images"])

# UPLOAD_DIR = Path("uploads")
# UPLOAD_DIR.mkdir(exist_ok=True)  # Ensure the upload directory exists


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

    # 파일 저장 처리
    file_path, source_type = await handle_file_or_url(file, url)

    # ReviewImage 객체 생성 및 DB에 저장
    uploaded_image = ReviewImage(
        review_id=review_id,
        filepath=str(file_path),
        source_type=source_type.value,
    )
    await image_repo.save_image(uploaded_image)

    # 해당 리뷰의 모든 이미지 조회
    query = select(ReviewImage).where(ReviewImage.review_id == review_id).order_by(ReviewImage.id)  # type: ignore
    result = await image_repo.session.execute(query)
    all_images = result.unique().scalars().all()

    if not all_images:
        raise HTTPException(status_code=404, detail="No images found for the given review")

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


# 이미지 삭제 엔드포인트
@image_router.delete("/delete", response_model=dict)
async def delete_images(
    file_names: list[str],
    user_id: str = Depends(authenticate),
    image_repo: ReviewRepo = Depends(),
    user_repo: UserRepository = Depends(),
) -> dict[str, Any]:
    user = await user_repo.get_user_by_id(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 삭제 결과 저장
    deleted_files = []
    not_found_files = []

    for file_name in file_names:
        query = select(ReviewImage).where(ReviewImage.filepath.contains(file_name))  # type: ignore
        result = await image_repo.session.execute(query)
        image = result.unique().scalar_one_or_none()

        if not image:
            not_found_files.append(file_name)
            continue
        # 로컬 파일삭제
        if image.source_type == ImageSourceType.UPLOAD.value:
            file_path = Path(image.filepath)
            if file_path.exists():
                file_path.unlink()
        # 데이터 베이스에서 이미지 삭제
        await image_repo.delete_image(image.id)
        deleted_files.append(file_name)

    return {
        "message": "Image deleted completed",
        "deleted_files": deleted_files,
        "not_found_files": not_found_files,
    }
