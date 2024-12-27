from fastapi import FastAPI
from fastapi.security import HTTPBearer

from src.user.router.router import router

app = FastAPI()
security = HTTPBearer()

app.include_router(router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str) -> dict[str, str]:
    return {"message": f"Hello {name}"}
