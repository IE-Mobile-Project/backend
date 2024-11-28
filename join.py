from fastapi import FastAPI
from fastapi_socketio import SocketManager
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 或指定允许的域名列表
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

socket_manager = SocketManager(app=app, mount_location="/socket.io/")


@app.get("/")
async def root():
    return {"message": "Server is running"}

# Socket.IO 事件处理：客户端连接
@socket_manager.on('connect')
async def connect(sid, environ):
    print(sid)
    print(f"Client {sid} connected")

# Socket.IO 事件处理：客户端断开连接
@socket_manager.on('disconnect')
async def disconnect(sid):
    print(f"Client {sid} disconnected")

@socket_manager.on("send_message")
async def send_message(sid, data):
    room_id = data["room_id"]
    user_id = data["user_id"]
    message = data["message"]
    print(sid)
    response = {"error": "In fact it's not an error"}
    print(response)
    if "error" in response:
        await socket_manager.emit("error", response["error"], to=sid)
        return

    # 广播消息给房间的所有用户
    await socket_manager.emit("new_message", {
        "room_id": room_id,
        "message": {"role_id": response["role_id"], "message": message},
        "last_messages": response["last_messages"]
    }, to=room_id)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
