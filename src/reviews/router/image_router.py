from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import requests  # type: ignore
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlmodel import select

from src.reviews.dtos.response import ReviewImageResponse, UploadImageResponse
from src.reviews.models.models import ImageSourceType, Review, ReviewImage
from src.reviews.repo import review_repo
from src.reviews.repo.review_repo import ReviewImageManager, ReviewRepo
from src.reviews.services.image_utils import handle_file_or_url, process_image_upload
from src.user.repo.repository import UserRepository
from src.user.services.authentication import authenticate

image_router = APIRouter(prefix="/images", tags=["Images"])

# UPLOAD_DIR = Path("uploads")
# UPLOAD_DIR.mkdir(exist_ok=True)  # Ensure the upload directory exists


@image_router.post("/upload", response_model=UploadImageResponse)
async def upload_images(
    file: Optional[UploadFile] = None,
    url: Optional[str] = None,
    user_id: str = Depends(authenticate),
    user_repo: UserRepository = Depends(),
) -> UploadImageResponse:

    # 사용자 인증 확인
    user = await user_repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    # 파일 업로드 처리
    uploaded_url, source_type = await handle_file_or_url(file=file, url=url)

    # `ReviewImageResponse` 생성
    uploaded_image = ReviewImageResponse(
        id=0,  # 업로드된 이미지는 아직 DB에 저장되지 않았으므로 임시로 0 설정
        review_id=0,  # 리뷰 ID가 없는 경우 0으로 설정
        filepath=uploaded_url,
        source_type=source_type.value,  # type: ignore
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    # 응답 생성
    return UploadImageResponse(
        uploaded_image=uploaded_image,
        all_images=[uploaded_image],  # 현재는 업로드된 이미지만 포함
        uploaded_url=uploaded_url,
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
