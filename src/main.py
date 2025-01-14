from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer

from src.reviews.repo.review_repo import ReviewRepo
from src.reviews.router.comment_router import comment_router
from src.reviews.router.image_router import image_router
from src.reviews.router.review_router import review_router
from src.reviews.router.websocket_router import websocket_router
from src.reviews.services.image_utils import start_scheduler, stop_scheduler
from src.travel.router.travel_router import router as travel_router
from src.user.router.router import router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # 시작 이벤트
    print("Lifespan started")  # 디버깅용

    review_repo = ReviewRepo()  # ReviewRepo 인스턴스 생성
    start_scheduler(review_repo)  # 스케줄러 시작

    yield  # lifespan의 중간 작업 실행

    # 종료 이벤트
    stop_scheduler()  # 스케줄러 종료
    print("Lifespan ended")  # 디버깅용


# FastAPI 애플리케이션 생성
app = FastAPI(lifespan=lifespan)
security = HTTPBearer()

# 허용할 출처(origin) 리스트
origins = ["*"]  # 모든 출처 허용

app.add_middleware(
    CORSMiddleware,
    allow_origins="http://localhost:3000",  # 허용할 출처 목록
    allow_credentials=True,  # 쿠키 포함 요청 허용
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 HTTP 헤더 허용
)

app.include_router(router)
app.include_router(travel_router)
app.include_router(review_router)
app.include_router(comment_router)
app.include_router(image_router)
app.include_router(websocket_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str) -> dict[str, str]:
    return {"message": f"Hello {name}"}
