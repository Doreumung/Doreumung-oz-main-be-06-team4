import hashlib
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Generator
from unittest.mock import MagicMock, patch

import boto3
import pytest
import requests_mock
from fastapi import HTTPException, UploadFile
from isort.parse import file_contents
from moto import mock_aws as mock_s3
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src import TravelRoute, User  # type: ignore
from src.reviews.dtos.response import ReviewImageResponse, UploadImageResponse
from src.reviews.models.models import ImageSourceType, Review, ReviewImage
from src.reviews.repo.review_repo import ReviewRepo
from src.reviews.router.image_router import upload_images
from src.reviews.services.image_utils import handle_file_or_url
from src.user.repo.repository import UserRepository

# Mock 환경 변수 설정
AWS_REGION = "ap-northeast-2"
BUCKET_NAME = "doreumung-06"


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


@pytest.fixture
def mock_s3_bucket() -> Generator[boto3.client, None, None]:
    """모킹된 S3 버킷 생성"""
    with mock_s3():
        s3 = boto3.client("s3", region_name=AWS_REGION)
        s3.create_bucket(
            Bucket=BUCKET_NAME,
            CreateBucketConfiguration={
                "LocationConstraint": AWS_REGION,
            },
        )
        yield s3


@pytest.mark.asyncio
async def test_upload_file_to_s3(mock_s3_bucket: boto3.client) -> None:
    """파일을 S3에 업로드하는 기능 테스트"""
    # 가상 파일 생성
    file_content = b"test content"
    test_file = UploadFile(filename="test_image.jpg", file=BytesIO(file_content))

    # S3에 파일 업로드
    s3_url, source_type = await handle_file_or_url(file=test_file, url=None)

    # 결과 검증
    expected_bucket_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/"
    assert source_type == ImageSourceType.UPLOAD
    assert s3_url.startswith(expected_bucket_url), f"Expected URL to start with {expected_bucket_url}, got {s3_url}"


@pytest.mark.asyncio
async def test_upload_url_to_s3(mock_s3_bucket: boto3.client, requests_mock: requests_mock.Mocker) -> None:
    """URL에서 파일을 다운로드하여 S3에 업로드하는 기능 테스트"""
    # Mock URL 설정
    file_content = b"test url content"
    test_url = "https://example.com/test_image.jpg"
    requests_mock.get(test_url, content=file_content)
    requests_mock.head(test_url, headers={"Content-Length": str(len(file_content))})

    # URL 처리 및 S3 업로드
    s3_url, source_type = await handle_file_or_url(file=None, url=test_url)

    # 결과 검증
    expected_bucket_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/"
    assert source_type == ImageSourceType.LINK
    assert s3_url.startswith(expected_bucket_url), f"Expected URL to start with {expected_bucket_url}, got {s3_url}"


# # url 업로드 테스트
#
#
# @pytest.mark.asyncio
# @patch("src.reviews.router.image_router.requests.get")
# async def test_upload_image_from_url(
#     mock_get: MagicMock,
#     async_session: AsyncSession,
#     setup_data: User,
#     setup_travelroute: TravelRoute,
# ) -> None:
#     """URL에서 이미지를 가져와 S3에 업로드하는 기능 테스트"""
#     with mock_s3():
#         # S3 클라이언트 생성
#         s3 = boto3.client("s3", region_name=AWS_REGION)
#         s3.create_bucket(
#             Bucket=BUCKET_NAME,
#             CreateBucketConfiguration={"LocationConstraint": AWS_REGION},
#         )
#
#         # 테스트 데이터 설정
#         user = setup_data
#         travel_route = setup_travelroute
#         seoul_tz = timezone(timedelta(hours=9))
#
#         review = Review(
#             id=1,
#             user_id=user.id,
#             travel_route_id=travel_route.id,
#             title="Test review title",
#             rating=4.5,
#             content="Test review content",
#             created_at=datetime.now(seoul_tz),
#             updated_at=datetime.now(seoul_tz),
#         )
#         async_session.add(review)
#         await async_session.commit()
#
#         # Mock requests.get
#         file_content = b"mock image content"
#         mock_response = MagicMock()
#         mock_response.status_code = 200
#         mock_response.content = file_content
#         mock_response.raw = BytesIO(file_content)
#         mock_get.return_value = mock_response
#
#         # URL 업로드 테스트 데이터
#         test_url = "https://example.com/test_image.jpg"
#
#         # 레포지토리 생성
#         review_repo = ReviewRepo(async_session)
#         user_repo = UserRepository(async_session)
#
#         # 엔드포인트 호출
#         response = await upload_images(
#             review_id=review.id,
#             file=None,
#             url=test_url,
#             user_id=user.id,
#             image_repo=review_repo,
#             user_repo=user_repo,
#         )
#
#         # 응답 데이터 검증
#         uploaded_url = response.uploaded_image.filepath
#         assert uploaded_url.startswith(f"https://{BUCKET_NAME}.s3.amazonaws.com/")
#         assert response.uploaded_image.source_type == ImageSourceType.LINK.value
#
#         # S3 파일 키 확인
#         s3_key = uploaded_url.split("/")[-1]
#         objects_in_s3 = s3.list_objects_v2(Bucket=BUCKET_NAME).get("Contents", [])
#         keys_in_s3 = [obj["Key"] for obj in objects_in_s3]
#
#         print(f"Uploaded Key: {s3_key}")
#         print("S3 Objects:", keys_in_s3)
#
#         assert s3_key in keys_in_s3, f"{s3_key} not found in S3 bucket"
#         s3_object = s3.get_object(Bucket=BUCKET_NAME, Key=s3_key)
#         assert s3_object["Body"].read() == file_content
