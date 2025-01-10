from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer

from src.reviews.router.comment_router import comment_router
from src.reviews.router.image_router import image_router
from src.reviews.router.review_router import review_router
from src.travel.router.travel_router import router as travel_router
from src.user.router.router import router

app = FastAPI()
security = HTTPBearer()

# 허용할 출처(origin) 리스트
origins = ["*"]  # 모든 출처 허용

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 허용할 출처 목록
    allow_credentials=True,  # 쿠키 포함 요청 허용
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 HTTP 헤더 허용
)

app.include_router(router)
app.include_router(travel_router)
app.include_router(review_router)
app.include_router(comment_router)
app.include_router(image_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str) -> dict[str, str]:
    return {"message": f"Hello {name}"}
