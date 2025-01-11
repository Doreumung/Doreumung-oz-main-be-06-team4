# from typing import List
#
# from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession
#
# from src import Like
# from src.reviews.repo.like_repo import LikeRepo
# from src.user.services.authentication import websocket_authenticate
#
# app = FastAPI()
#
#
# class ConnectionManager:
#     def __init__(self):
#         self.active_connections: List[WebSocket] = []
#
#     async def connect(self, websocket: WebSocket):
#         await websocket.accept()
#         self.active_connections.append(websocket)
#
#     def disconnect(self, websocket: WebSocket):
#         self.active_connections.remove(websocket)
#
#     async def broadcast(self, message: str):
#         for connection in self.active_connections:
#             await connection.send_text(message)
#
#
# manager = ConnectionManager()
#
#
# @app.websocket("/ws/likes")
# async def websocket_endpoint(websocket: WebSocket, like_repo: LikeRepo = Depends(), session: AsyncSession = Depends()):
#     query_params = websocket.query_params
#     protocol = websocket.headers["sec-websocket-protocol"]
#
#     user_id = None
#     if protocol and protocol[:7] == "Bearer ":
#         token = protocol[7:]
#         user_id = websocket_authenticate(token)  # jwt access token 인증
#
#     review_id = query_params.get("reviewId")  #
#     if review_id is None:
#         await websocket.close()
#         return
#     try:
#         review = await like_repo.get_by_id(review_id)  # type:ignore
#     except HTTPException:
#         await websocket.close()
#         return
#     is_author = review.user_id == user_id if user_id else None  # 작성자 유무
#     is_liked = None
#     if user_id:
#         # 해당게시물 like 누름 유무
#         # 이거 scalar 값 변환해줘야함
#         is_liked = await session.execute(select(Like).where(Like.review_id == review_id, Like.user_id == user_id))
#     await manager.connect(websocket)
#     await websocket.send_json({"reviewId": review_id, "likes": review.like_count, "is_liked": True})
#     try:
#         while True:
#             data = await websocket.receive_json()  # 클라이언트에서 메시지 수신
#             # is_liked로 눌름,취소 구분하여 코딩
#             await manager.broadcast(data)  # 모든 클라이언트에 메시지 전송
#     except WebSocketDisconnect:
#         manager.disconnect(websocket)
