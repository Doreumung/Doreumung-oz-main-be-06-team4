# from fastapi import FastAPI, WebSocket, WebSocketDisconnect
# from typing import List
#
# app = FastAPI()
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
# manager = ConnectionManager()
#
# @app.websocket("/ws/likes")
# async def websocket_endpoint(websocket: WebSocket):
#     query_params = websocket.query_params
#     review_id = query_params.get("reviewId")
#
#     if not review_id or review_id not in likes_db:
#         await websocket.close()
#         return
#
#     await manager.connect(websocket)
#     await websocket.send_json({"reviewId": review_id, "likes": likes_db[review_id]})
#     try:
#         while True:
#             data = await websocket.receive_json()  # 클라이언트에서 메시지 수신
#             await manager.broadcast(data)         # 모든 클라이언트에 메시지 전송
#     except WebSocketDisconnect:
#         manager.disconnect(websocket)
