import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Set
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from src.reviews.dtos.response import ReviewImageResponse
from src.reviews.models.models import ImageSourceType, Review, ReviewImage


# 유틸리티 함수: 정렬 컬럼 유효성 검증
def validate_order_by(order_by: str, valid_columns: Set[str]) -> Any:
    if order_by not in valid_columns:
        raise HTTPException(status_code=400, detail=f"Invalid order_by value: {order_by}")
    return getattr(Review, order_by)
