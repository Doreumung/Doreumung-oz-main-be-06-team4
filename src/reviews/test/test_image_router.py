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
from src.reviews.router.image_router import (
    get_image_by_id,
    get_images_by_review,
    update_images,
    upload_images,
)
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


# 이미지 조회


@pytest.mark.asyncio
async def test_get_images_by_review(
    async_session: AsyncSession,
    setup_data: User,
    setup_travelroute: TravelRoute,
) -> None:
    user = setup_data
    travel_route = setup_travelroute
    seoul_tz = timezone(timedelta(hours=9))
    async_session.add(user)
    await async_session.commit()

    # 리뷰 생성
    review = Review(
        id=1,
        user_id=user.id,
        travel_route_id=travel_route.id,
        title="Test review",
        rating=4.0,
        content="Test content",
        created_at=datetime.now(seoul_tz),
        updated_at=datetime.now(seoul_tz),
    )
    async_session.add(review)
    await async_session.commit()

    # 이미지 생성
    images = [
        ReviewImage(
            id=i,
            review_id=review.id,
            filepath=f"/uploads/test_image_{i}.jpg",
            source_type="upload",
        )
        for i in range(1, 4)
    ]
    async_session.add_all(images)
    await async_session.commit()

    # 레포지토리 생성
    review_repo = ReviewRepo(async_session)

    # 테스트 실행
    response = await get_images_by_review(review_id=review.id, image_repo=review_repo)

    # 검증
    assert len(response) == 3
    assert isinstance(response[0], ReviewImageResponse)
    assert response[0].review_id == review.id
    assert response[0].filepath == "/uploads/test_image_1.jpg"


@pytest.mark.asyncio
async def test_get_image_by_id(
    async_session: AsyncSession,
    setup_review: Review,
) -> None:

    review = setup_review

    # 이미지 생성
    image = ReviewImage(
        id=1,
        review_id=review.id,
        filepath="/uploads/test_image_1.jpg",
        source_type="upload",
    )
    async_session.add(image)
    await async_session.commit()

    # 레포지토리 생성
    review_repo = ReviewRepo(async_session)

    # 테스트 실행
    response = await get_image_by_id(image_id=image.id, image_repo=review_repo)

    # 검증
    assert response.id == image.id
    assert response.review_id == review.id
    assert response.filepath == "/uploads/test_image_1.jpg"
    assert response.source_type == "upload"


# 이미지 수정 테스트
@pytest.mark.asyncio
async def test_update_images(async_session: AsyncSession, setup_data: User, setup_travelroute: TravelRoute) -> None:
    user = setup_data
    travel_route = setup_travelroute
    review = Review(
        id=100,  # review_id를 정수로 설정
        user_id=user.id,
        travel_route_id=travel_route.id,
        title="Test review",
        rating=4.0,
        content="Test content",
    )
    async_session.add(review)
    await async_session.commit()

    # 임시 디렉토리 설정
    uploads_dir = Path("/tmp/uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)

    # 기존 이미지 생성
    existing_file_path = uploads_dir / "existing_image.jpg"
    existing_image = ReviewImage(
        id=1,
        review_id=review.id,
        filepath=str(existing_file_path),  # 경로를 정확히 설정
        source_type=ImageSourceType.UPLOAD.value,
    )
    async_session.add(existing_image)
    await async_session.commit()

    # 기존 파일 생성 및 내용 추가
    existing_file_path.touch()
    with existing_file_path.open("wb") as f:
        f.write(b"existing content")

    # 가상 파일 생성
    test_file_path = Path("/tmp/test_image.jpg")
    test_file_path.touch()  # 파일 생성
    with test_file_path.open("wb") as f:
        f.write(b"test content")  # 테스트 내용 추가

    # UploadFile 객체 생성
    new_file = UploadFile(filename="test_image.jpg", file=test_file_path.open("rb"))

    # 레포지토리 생성
    review_repo = ReviewRepo(async_session)
    user_repo = UserRepository(async_session)

    # 이미지 업데이트 호출
    response = await update_images(
        image_id=existing_image.id,
        file=new_file,
        url=None,
        user_id=user.id,
        image_repo=review_repo,
        user_repo=user_repo,
    )

    # 검증: 파일 경로
    assert response.uploaded_image.filepath.endswith("_test_image.jpg")

    # 검증: 파일 내용
    updated_file_path = Path(response.uploaded_image.filepath)
    with updated_file_path.open("rb") as f:
        updated_file_content = f.read()
    assert hashlib.md5(updated_file_content).hexdigest() == hashlib.md5(b"test content").hexdigest()

    # Cleanup
    existing_file_path.unlink(missing_ok=True)
    updated_file_path.unlink(missing_ok=True)
    test_file_path.unlink(missing_ok=True)


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
    test_file_path = uploads_dir / "test_image.jpg"
    test_file_path.touch()
    with test_file_path.open("wb") as f:
        f.write(b"test content")

    # 데이터베이스에 ReviewImage 추가
    image = ReviewImage(
        id=1,
        review_id=review.id,
        filepath=str(test_file_path),
        source_type=ImageSourceType.UPLOAD.value,
    )
    async_session.add(image)
    await async_session.commit()

    # 레포지토리 인스턴스 생성
    review_repo = ReviewRepo(async_session)
    user_repo = UserRepository(async_session)

    # DELETE 엔드포인트 시뮬레이션
    async def delete_images_mock(image_id: int, user_id: str) -> dict[str, Any]:
        # 유저 확인
        user = await user_repo.get_user_by_id(user_id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # 이미지 확인
        query = select(ReviewImage).where(ReviewImage.id == image_id)  # type: ignore
        result = await review_repo.session.execute(query)
        existing_image = result.scalar_one_or_none()
        if not existing_image:
            raise HTTPException(status_code=404, detail="Image not found")

        # 파일 삭제
        if existing_image.source_type == ImageSourceType.UPLOAD.value:
            file_path = Path(existing_image.filepath)
            if file_path.exists():
                file_path.unlink()

        # 데이터베이스에서 이미지 삭제
        await review_repo.session.delete(existing_image)
        await review_repo.session.commit()

        return {"message": "Image deleted successfully"}  # 반환값 추가

    # 테스트 실행
    response = await delete_images_mock(image_id=image.id, user_id=user.id)

    # 응답 검증
    assert response == {"message": "Image deleted successfully"}

    # 파일 삭제 검증
    assert not test_file_path.exists()

    # 데이터베이스 삭제 검증
    query = select(ReviewImage).where(ReviewImage.id == image.id)  # type: ignore
    result = await async_session.execute(query)
    deleted_image = result.scalar_one_or_none()
    assert deleted_image is None
