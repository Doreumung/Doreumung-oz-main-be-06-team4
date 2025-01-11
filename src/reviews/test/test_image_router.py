import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src import TravelRoute, User  # type: ignore
from src.reviews.dtos.response import ReviewImageResponse, UploadImageResponse
from src.reviews.models.models import ImageSourceType, Review, ReviewImage
from src.reviews.repo.review_repo import ReviewRepo
from src.reviews.router.image_router import upload_images
from src.user.repo.repository import UserRepository


@pytest.mark.asyncio
async def test_upload_images(
    async_session: AsyncSession,
    setup_data: User,
    setup_travelroute: TravelRoute,
) -> None:
    # Setup: 주어진 User와 TravelRoute 사용하여 테스트용 데이터 설정
    user = setup_data
    travel_route = setup_travelroute
    seoul_tz = timezone(timedelta(hours=9))

    # 사용자와 여행 정보를 데이터베이스에 추가
    async_session.add(user)
    await async_session.commit()

    # Review 객체 추가
    review = Review(
        id=1,
        user_id=user.id,
        travel_route_id=travel_route.id,
        title="Test review title",
        rating=4.5,
        content="Test review content",
        created_at=datetime.now(seoul_tz),
        updated_at=datetime.now(seoul_tz),
    )
    async_session.add(review)
    await async_session.commit()

    # 가상 파일 생성
    test_file_path = Path("/tmp/test_image.jpg")
    test_file_path.touch()  # 파일 생성
    with test_file_path.open("wb") as f:
        f.write(b"test content")  # 간단한 테스트 내용 추가

    # UploadFile 객체 생성
    file = UploadFile(filename="test_image.jpg", file=test_file_path.open("rb"))

    # 레포지토리 생성
    review_repo = ReviewRepo(async_session)
    user_repo = UserRepository(async_session)

    # 엔드포인트 호출
    response = await upload_images(
        review_id=review.id,
        file=file,
        url=None,
        user_id=user.id,
        image_repo=review_repo,
        user_repo=user_repo,
    )

    # 응답 데이터 검증
    assert isinstance(response, UploadImageResponse)
    assert response.uploaded_image.review_id == review.id
    assert response.uploaded_image.filepath.endswith("test_image.jpg")
    assert response.uploaded_image.source_type == "upload"

    # DB에 저장된 데이터 검증
    uploaded_image = await async_session.get(ReviewImage, response.uploaded_image.id)
    assert uploaded_image is not None
    assert uploaded_image.review_id == review.id
    assert uploaded_image.filepath.endswith("test_image.jpg")
    assert uploaded_image.source_type == "upload"

    # 파일 삭제
    if test_file_path.exists():
        test_file_path.unlink()


# url 업로드 테스트


@pytest.mark.asyncio
@patch("src.reviews.router.image_router.requests.get")
async def test_upload_image_from_url(
    mock_get: MagicMock,
    async_session: AsyncSession,
    setup_data: User,
    setup_travelroute: TravelRoute,
) -> None:
    # Setup: 주어진 User와 TravelRoute 사용하여 테스트용 데이터 설정
    user = setup_data
    travel_route = setup_travelroute
    seoul_tz = timezone(timedelta(hours=9))

    # Review 객체 추가
    review = Review(
        id=1,
        user_id=user.id,
        travel_route_id=travel_route.id,
        title="Test review title",
        rating=4.5,
        content="Test review content",
        created_at=datetime.now(seoul_tz),
        updated_at=datetime.now(seoul_tz),
    )
    async_session.add(review)
    await async_session.commit()

    # Mock requests.get
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"mock image content"
    mock_get.return_value = mock_response

    # URL 업로드 테스트 데이터
    test_url = "https://example.com/test_image.jpg"

    # 레포지토리 생성
    review_repo = ReviewRepo(async_session)
    user_repo = UserRepository(async_session)

    # 엔드포인트 호출
    response = await upload_images(
        review_id=review.id,
        file=None,
        url=test_url,
        user_id=user.id,
        image_repo=review_repo,
        user_repo=user_repo,
    )

    # 응답 데이터 검증
    assert response.uploaded_image.review_id == review.id
    assert response.uploaded_image.filepath.endswith("test_image.jpg")
    assert response.uploaded_image.source_type == "link"

    # DB에 저장된 데이터 확인
    query = await async_session.execute(select(ReviewImage).where(ReviewImage.review_id == review.id))  # type: ignore
    saved_images = query.scalars().all()
    assert len(saved_images) == 1
    assert saved_images[0].filepath.endswith("test_image.jpg")
    assert saved_images[0].source_type == "link"


# 삭제 테스트
@pytest.mark.asyncio
async def test_delete_images(async_session: AsyncSession, setup_data: User, setup_travelroute: TravelRoute) -> None:
    # 테스트 유저 및 리뷰 데이터 생성
    user = setup_data
    travel_route = setup_travelroute
    review = Review(
        id=100,
        user_id=user.id,
        travel_route_id=travel_route.id,
        title="Test Review",
        rating=4.0,
        content="This is a test review.",
    )
    async_session.add(review)
    await async_session.commit()

    # 임시 디렉토리 설정
    uploads_dir = Path("/tmp/uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)

    # 테스트 이미지 생성
    test_file_path_1 = uploads_dir / "test_image_1.jpg"
    test_file_path_2 = uploads_dir / "test_image_2.jpg"
    test_file_path_1.touch()
    test_file_path_2.touch()
    with test_file_path_1.open("wb") as f1, test_file_path_2.open("wb") as f2:
        f1.write(b"test content 1")
        f2.write(b"test content 2")

    # 데이터베이스에 ReviewImage 추가
    image_1 = ReviewImage(
        id=1,
        review_id=review.id,
        filepath=str(test_file_path_1),
        source_type=ImageSourceType.UPLOAD.value,
    )
    image_2 = ReviewImage(
        id=2,
        review_id=review.id,
        filepath=str(test_file_path_2),
        source_type=ImageSourceType.UPLOAD.value,
    )
    async_session.add_all([image_1, image_2])
    await async_session.commit()

    # 레포지토리 인스턴스 생성
    review_repo = ReviewRepo(async_session)
    user_repo = UserRepository(async_session)

    # DELETE 엔드포인트 시뮬레이션
    async def delete_images_mock(file_names: list[str], user_id: str) -> dict[str, Any]:
        # 유저 확인
        user = await user_repo.get_user_by_id(user_id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        deleted_files = []
        not_found_files = []

        for file_name in file_names:
            # 파일명으로 이미지 검색
            query = select(ReviewImage).where(ReviewImage.filepath.like(f"%{file_name}"))  # type: ignore
            result = await review_repo.session.execute(query)
            existing_image = result.scalar_one_or_none()

            if not existing_image:
                not_found_files.append(file_name)
                continue

            # 파일 삭제
            if existing_image.source_type == ImageSourceType.UPLOAD.value:
                file_path = Path(existing_image.filepath)
                if file_path.exists():
                    file_path.unlink()

            # 데이터베이스에서 이미지 삭제
            await review_repo.session.delete(existing_image)
            await review_repo.session.commit()
            deleted_files.append(file_name)

        return {
            "message": "Image deletion completed",
            "deleted_files": deleted_files,
            "not_found_files": not_found_files,
        }

    # 테스트 실행
    file_names = ["test_image_1.jpg", "test_image_2.jpg"]
    response = await delete_images_mock(file_names=file_names, user_id=user.id)

    # 응답 검증
    assert response["message"] == "Image deletion completed"
    assert "test_image_1.jpg" in response["deleted_files"]
    assert "test_image_2.jpg" in response["deleted_files"]
    assert not response["not_found_files"]

    # 파일 삭제 검증
    assert not test_file_path_1.exists()
    assert not test_file_path_2.exists()

    # 데이터베이스 삭제 검증
    query = select(ReviewImage).where(ReviewImage.filepath.in_([str(test_file_path_1), str(test_file_path_2)]))  # type: ignore
    result = await async_session.execute(query)
    deleted_images = result.scalars().all()
    assert not deleted_images
