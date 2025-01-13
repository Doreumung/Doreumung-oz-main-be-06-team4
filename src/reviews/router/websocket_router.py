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
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from uvicorn.protocols.utils import ClientDisconnected

from src import Comment, Like, Review  # type:ignore
from src.config.database.connection_async import get_async_session
from src.reviews.repo.like_repo import LikeRepo
from src.reviews.repo.review_repo import CommentRepo, ReviewRepo
from src.user.services.authentication import websocket_authenticate

websocket_router = APIRouter()


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        print("현재 연결된 웹소켓의 수", len(self.active_connections))

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


@websocket_router.websocket("/ws/likes")
async def like_websocket_endpoint(
    websocket: WebSocket,
    review_repo: ReviewRepo = Depends(),
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
            if data.get("type") == "like":
                async for async_session in get_async_session():
                    review_repo = ReviewRepo(async_session)
                    review = await review_repo.get_review_by_id(int(review_id))
                    like_repo = LikeRepo(async_session)
                    original_like_count = review.like_count  # type:ignore
                    if data.get("is_liked"):
                        try:
                            like = Like(user_id=data.get("user_id"), review_id=int(data.get("review_id")))
                            await like_repo.save(like)
                            await async_session.execute(
                                update(Review)
                                .where(Review.id == int(data.get("review_id")))
                                .values(like_count=Review.like_count + 1)
                            )
                            await async_session.refresh(review)
                            await async_session.commit()
                            data["like_count"] = review.like_count  # type:ignore
                        except Exception as e:
                            print(e)
                            await async_session.rollback()
                            data["like_count"] = original_like_count
                    else:
                        like = await like_repo.get_by_user_review_id(
                            user_id=data.get("user_id"), review_id=int(data.get("review_id"))
                        )
                        if like:
                            try:
                                await like_repo.delete(like)
                                await async_session.execute(
                                    update(Review)
                                    .where(Review.id == int(data.get("review_id")))
                                    .values(like_count=Review.like_count - 1)
                                )
                                await async_session.refresh(review)
                                await async_session.commit()
                                data["like_count"] = review.like_count  # type:ignore
                            except Exception as e:
                                print(e)
                                await async_session.rollback()
                                data["like_count"] = original_like_count
                        else:
                            data["like_count"] = original_like_count

            elif data.get("type") == "comment":
                async for async_session in get_async_session():
                    comment_repo = CommentRepo(async_session)
                    if data.get("method") == "POST":
                        nickname = data.get("nickname")
                        content = data.get("content")
                        comment = Comment(
                            user_id=data.get("user_id"), review_id=int(review_id), nickname=nickname, content=content
                        )
                        await comment_repo.create_comment(comment)
                    elif data.get("method") == "PATCH":
                        comment = await comment_repo.get_comment_by_id(comment_id=int(data.get("comment_id")))
                        comment.content = data.get("content")
                        await comment_repo.create_comment(comment)
                    elif data.get("method") == "DELETE":
                        await comment_repo.delete_comment(int(data.get("comment_id")))
                        data["review_id"] = review_id

            await manager.broadcast(data)  # 모든 클라이언트에 메시지 전송
    except WebSocketDisconnect as e:
        print(e)
        print("WebSocket disconnected")
        manager.disconnect(websocket)
