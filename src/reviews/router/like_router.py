import json
from typing import List

from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uvicorn.protocols.utils import ClientDisconnected

from src import Like  # type:ignore
from src.config.database.connection_async import get_async_session
from src.reviews.repo.like_repo import LikeRepo
from src.reviews.repo.review_repo import ReviewRepo
from src.user.services.authentication import websocket_authenticate

like_router = APIRouter()


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str) -> None:
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Failed to send message: {e}")
                self.disconnect(connection)


manager = ConnectionManager()


@like_router.websocket("/ws/likes")
async def websocket_endpoint(
    websocket: WebSocket,
    review_repo: ReviewRepo = Depends(),
    like_repo: LikeRepo = Depends(),
    session: AsyncSession = Depends(get_async_session),
) -> None:
    query_params = websocket.query_params
    review_id = query_params.get("review_id")
    if review_id is None:
        await websocket.close()
        return
    try:
        review = await review_repo.get_review_by_id(int(review_id))
    except HTTPException:
        await websocket.close()
        return
    # is_author = review.user_id == user_id if user_id else None  # 작성자 유무
    # if user_id:
    #     # 해당게시물 like 누름 유무
    #     # 이거 scalar 값 변환해줘야함
    #     is_liked = await session.execute(select(Like).where(Like.review_id == review_id, Like.user_id == user_id))
    await manager.connect(websocket)
    await websocket.send_json({"review_id": review_id, "like_count": review.like_count})  # type:ignore
    try:
        while True:
            data = await websocket.receive_json()
            if type(data) == str:
                data = json.loads(data)  # 클라이언트에서 메시지 수신
            if data.get("is_liked"):
                data["like_count"] = review.like_count  # type:ignore
                like = await like_repo.get_by_user_review_id(
                    user_id=data.get("user_id"), review_id=int(data.get("review_id"))
                )
                if not like:
                    like = Like(user_id=data.get("user_id"), review_id=int(data.get("review_id")))
                    await like_repo.save(like)
                    review.like_count += 1  # type:ignore
                    review = await review_repo.save_review(review)  # type:ignore
                    data["like_count"] = review.like_count  # type:ignore
            else:
                data["like_count"] = review.like_count  # type:ignore
                like = await like_repo.get_by_user_review_id(
                    user_id=data.get("user_id"), review_id=int(data.get("review_id"))
                )
                if like:
                    await like_repo.delete(like)
                    review.like_count -= 1  # type:ignore
                    review = await review_repo.save_review(review)  # type:ignore
                    data["like_count"] = review.like_count  # type:ignore
            # is_liked로 눌름,취소 구분하여 코딩
            await manager.broadcast(data)  # 모든 클라이언트에 메시지 전송
    except WebSocketDisconnect:
        print("WebSocket disconnected")
        manager.disconnect(websocket)
