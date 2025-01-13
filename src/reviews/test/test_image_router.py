import hashlib
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Generator, List
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import UUID

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
from src.reviews.router.image_router import delete_images, upload_images
from src.reviews.services.image_utils import handle_file_or_url
from src.user.repo.repository import UserRepository

# Mock 환경 변수 설정
AWS_REGION = "ap-northeast-2"
BUCKET_NAME = "doreumung-06"


@pytest.mark.asyncio
async def test_upload_images_handler() -> None:
    # `uploads/` 디렉토리 생성
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)

    # Mock UserRepository
    mock_user_repo = AsyncMock()
    mock_user_repo.get_user_by_id.return_value = Mock(id="user1")

    # Mock ImageRepository
    mock_image_repo = AsyncMock()
    mock_image_repo.save_image.return_value = ReviewImage(
        id=1,
        user_id="user1",
        filepath="uploads/user1/test_image.jpg",
        source_type=ImageSourceType.UPLOAD,
        is_temporary=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    # Mock 파일
    uploaded_file = Mock()
    uploaded_file.filename = "test_image.jpg"
    uploaded_file.file = Mock()
    uploaded_file.file.read = Mock(side_effect=[b"test data"] * 3 + [b""])  # S3 업로드와 파일 복사를 위한 Mock
    uploaded_file.file.tell = Mock(return_value=5 * 1024 * 1024)  # 파일 크기를 5MB로 설정
    uploaded_file.file.seek = Mock()  # seek 메서드 Mock

    # Mock S3 client
    with patch("src.reviews.services.image_utils.s3_client.upload_fileobj", Mock(return_value=None)):
        # 테스트 실행
        response = await upload_images(
            file=uploaded_file,
            url=None,
            user_id="user1",
            user_repo=mock_user_repo,
            image_repo=mock_image_repo,
        )

    # 응답 검증
    assert response.uploaded_image.id == 1
    assert response.uploaded_image.filepath == "uploads/user1/test_image.jpg"
    assert response.uploaded_image.source_type == "upload"


# 삭제 테스트
@pytest.mark.asyncio
async def test_delete_images_handler() -> None:
    # Mock 데이터
    mock_user_repo: AsyncMock = AsyncMock()
    mock_image_repo: AsyncMock = AsyncMock()

    mock_user_repo.get_user_by_id.return_value = AsyncMock(id="user1")
    file_names: List[str] = ["test_image.jpg", "s3_image.jpg"]
    s3_image_url: str = "https://bucket-name.s3.amazonaws.com/s3_image.jpg"

    mock_images: Dict[str, ReviewImage] = {
        "test_image.jpg": ReviewImage(
            id=1, filepath=f"/local/path/{file_names[0]}", source_type=ImageSourceType.UPLOAD
        ),
        "s3_image.jpg": ReviewImage(id=2, filepath=s3_image_url, source_type=ImageSourceType.UPLOAD),
    }

    async def mock_execute(query: Any) -> Mock:
        for file_name, image in mock_images.items():
            if file_name in query.compile(compile_kwargs={"literal_binds": True}).string:
                return Mock(unique=lambda: Mock(scalar_one_or_none=lambda: image))
        return Mock(unique=lambda: Mock(scalar_one_or_none=lambda: None))

    mock_image_repo.session.execute = mock_execute
    mock_image_repo.delete_image = AsyncMock()

    # 올바른 s3_client 경로로 수정
    with patch("src.reviews.services.image_utils.s3_client.delete_object", return_value=None) as mock_s3_delete, patch(
        "pathlib.Path.exists", return_value=True
    ), patch("pathlib.Path.unlink", return_value=None):

        response: Dict[str, Any] = await delete_images(
            file_names=file_names,
            user_id="user1",
            image_repo=mock_image_repo,
            user_repo=mock_user_repo,
        )

        mock_user_repo.get_user_by_id.assert_called_once_with(user_id="user1")
        mock_image_repo.delete_image.assert_any_call(1)
        mock_image_repo.delete_image.assert_any_call(2)

        assert response["message"] == "Image deleted completed"
        assert response["deleted_files"] == file_names
        assert response["not_found_files"] == []


@pytest.mark.asyncio
async def test_delete_images_handler_not_found() -> None:
    """
    Test delete_images function when no images are found for deletion.
    """
    # Mock 데이터
    mock_user_repo: AsyncMock = AsyncMock()
    mock_image_repo: AsyncMock = AsyncMock()

    # Mock 사용자 데이터
    mock_user_repo.get_user_by_id.return_value = AsyncMock(id="user1")

    # Mock 이미지 파일 이름
    file_names: List[str] = ["non_existent_image.jpg"]

    # Mock 실행 함수
    async def mock_execute(query: Any) -> Mock:
        return Mock(unique=lambda: Mock(scalar_one_or_none=lambda: None))  # 이미지 없음

    mock_image_repo.session.execute = mock_execute  # 쿼리 실행 Mock

    # 테스트 실행
    response: Dict[str, Any] = await delete_images(
        file_names=file_names,
        user_id="user1",
        image_repo=mock_image_repo,
        user_repo=mock_user_repo,
    )

    # Assertions
    mock_user_repo.get_user_by_id.assert_called_once_with(user_id="user1")
    assert response["message"] == "Image deleted completed"
    assert response["deleted_files"] == []
    assert response["not_found_files"] == file_names


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
    mock_image_repo = AsyncMock()

    s3_url, source_type = await handle_file_or_url(
        file=test_file, url=None, user_id="user1", image_repo=mock_image_repo
    )

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
    mock_image_repo = AsyncMock()

    s3_url, source_type = await handle_file_or_url(file=None, url=test_url, user_id="user1", image_repo=mock_image_repo)

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
