from contextlib import asynccontextmanager
from typing import AsyncGenerator, Callable, Generator, Tuple
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.main import app
from src.reviews.repo.review_repo import ReviewRepo
from src.reviews.services.image_utils import (
    cleanup_temporary_images,
    scheduler,
    start_scheduler,
    stop_scheduler,
)


@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    """
    FastAPI TestClient와 Mock 설정
    """
    with patch(
        "src.reviews.services.image_utils.start_scheduler", new_callable=MagicMock
    ) as mock_start_scheduler, patch(
        "src.reviews.services.image_utils.stop_scheduler", new_callable=MagicMock
    ) as mock_stop_scheduler, patch(
        "src.reviews.repo.review_repo.ReviewRepo", new_callable=AsyncMock
    ) as mock_review_repo:
        app = FastAPI(lifespan=mock_lifespan(mock_review_repo, mock_start_scheduler, mock_stop_scheduler))  # type: ignore
        with TestClient(app) as client:
            yield client, mock_start_scheduler, mock_stop_scheduler, mock_review_repo  # type: ignore


def mock_lifespan(
    mock_review_repo: Mock, mock_start_scheduler: Mock, mock_stop_scheduler: Mock
) -> Callable[[FastAPI], AsyncGenerator[None, None]]:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        mock_start_scheduler(mock_review_repo)  # Mock 호출
        yield
        mock_stop_scheduler()  # Mock 호출

    return lifespan  # type: ignore


def test_lifespan_startup_shutdown(test_client: Tuple[TestClient, Mock, Mock, Mock]) -> None:
    """
    Lifespan 이벤트 핸들러 테스트
    """
    client, mock_start_scheduler, mock_stop_scheduler, mock_review_repo = test_client

    # Mock 초기화
    mock_start_scheduler.reset_mock()

    # Lifespan 이벤트 트리거
    with client:
        pass

    # 호출 검증
    print(f"Mock calls: {mock_start_scheduler.call_args_list}")  # 호출 이력 출력
    assert mock_start_scheduler.call_count == 1, f"start_scheduler was called {mock_start_scheduler.call_count} times"
    mock_stop_scheduler.assert_called_once()


@pytest.mark.asyncio
async def test_cleanup_temporary_images() -> None:
    """
    cleanup_temporary_images 함수 테스트
    """
    # Mock ReviewRepo 생성
    mock_review_repo = AsyncMock()

    # Mock 이미지 데이터 생성
    mock_images = [
        MagicMock(id=1, filepath="temp_file_1.jpg", is_temporary=True),
        MagicMock(id=2, filepath="temp_file_2.jpg", is_temporary=True),
    ]

    # scalars().all() 호출 설정
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = mock_images
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_review_repo.session.execute.return_value = mock_result

    # delete_file과 delete_image 모킹
    async def mock_delete_file(image) -> None:  # type: ignore
        pass

    mock_review_repo.delete_image = AsyncMock()

    with patch("src.reviews.services.image_utils.delete_file", side_effect=mock_delete_file):
        await cleanup_temporary_images(mock_review_repo)

    # 삭제된 이미지 수 검증
    assert mock_review_repo.delete_image.call_count == len(mock_images)
