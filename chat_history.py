import random

import requests
from fastapi import FastAPI
from fastapi_socketio import SocketManager
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError

import time

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

# 配置 MongoDB
MONGO_DETAILS = "mongodb+srv://Assignment4:240423xdw@cluster0.qx6pn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = AsyncIOMotorClient(MONGO_DETAILS)
db = client["IEMS5722_project"]
chatroom_collection = db["chatroom"]
messages_collection = db["messages"]
room_messages_collection = db["room_messages"]
LLM_URL = '10.13.212.97'

Max_player = 5
Max_Round = 1


@app.get("/")
async def root():
    return {"message": "Server is running"}

# Socket.IO 事件处理：客户端连接
@socket_manager.on('connect')
async def connect(sid, environ):
    print(f"Client {sid} connected")

# Socket.IO 事件处理：客户端断开连接
@socket_manager.on('disconnect')
async def disconnect(sid):
    print(f"Client {sid} disconnected")

@app.get("/v1/chatroom/list")
async def get_waiting_chatrooms():
    chatrooms = await chatroom_collection.find({"status": "waiting"}).to_list(100)
    return {"code":0, "chatrooms": [{"chatroom_id": room["chatroom_id"], "chatroom_name": room["chatroom_name"]} for room in chatrooms]}


"""request"""
from typing import List, Optional, Text, Union, Dict
from pydantic import BaseModel, Field


class CreateRoomRequest(BaseModel):
    chatroom_name: str = Field(..., description="role")
    creator_id: str = Field(..., description="content")

@app.post("/v1/chatroom/create")
# async def create_chatroom(chatroom_name: str, creator_id: str):
async def create_chatroom(request:CreateRoomRequest):
    chatroom_name = request.chatroom_name
    creator_id = request.creator_id
    print({"chatroom name: ": chatroom_name, "creator_id": creator_id})
    while True:
        room_id = f"room_{random.randint(1, 10000)}"
        role_id = random.randint(1, Max_player)
        chatroom_data = {
            "chatroom_id": room_id,
            "chatroom_name": chatroom_name,
            "status": "waiting",
            "users": [{"user_id": creator_id, "role_id": role_id}],
            "score": []
        }

        try:
            await chatroom_collection.insert_one(chatroom_data)
            break  # 如果插入成功，退出循环
        except DuplicateKeyError:
            continue  # 重新生成 room_id
    print({"message": "Chatroom created", "chatroom_id": room_id, "role_id": role_id, "code": 0})
    return {"message": "Chatroom created", "chatroom_id": room_id, "role_id": role_id, "code": 0}



class JoinRoomRequest(BaseModel):
    room_id: str = Field(..., description="room_id")
    user_id: str = Field(..., description="user_id")

@app.post("/v1/chatroom/join")
async def join_room_http(request:JoinRoomRequest):
    room_id = request.room_id
    user_id = request.user_id
    response = await process_join_room(room_id, user_id)
    return response

async def process_join_room(room_id: str, user_id: str):
    # 核心逻辑
    chatroom = await chatroom_collection.find_one({"chatroom_id": room_id})
    if not chatroom:
        return {"error": "Chatroom not found", "code": 1}

    if chatroom["status"] != "waiting":
        print({"error": "Chatroom is not in waiting state"})
        return {"error": "Chatroom is not in waiting state", "code": 1}

    if any(user["user_id"] == user_id for user in chatroom["users"]):
        return {"error": "User already in chatroom", "code": 1}

    existing_roles = {user["role_id"] for user in chatroom["users"]}
    available_roles = set(range(1, Max_player+1)) - existing_roles
    if not available_roles:
        return {"error": "No roles available", "code": 1}
    role_id = random.choice(list(available_roles))

    await chatroom_collection.update_one(
        {"chatroom_id": room_id},
        {"$push": {"users": {"user_id": user_id, "role_id": role_id}}}
    )

    chatroom["users"].append({"user_id": user_id, "role_id": role_id})
    print(f"{room_id} join user: " + str({"user_id": user_id, "role_id": role_id}))
    if len(chatroom["users"]) == 3:
        # 剩余的位置填补llm
        existing_roles = {user["role_id"] for user in chatroom["users"]}
        available_roles = set(range(1, Max_player + 1)) - existing_roles
        print("available_ones:" + str(available_roles))
        for available_role_id in list(available_roles):
            await chatroom_collection.update_one(
                {"chatroom_id": room_id},
                {"$push": {"users": {"user_id": f"llm{available_role_id}", "role_id": available_role_id}}}
            )
            chatroom["users"].append({"user_id": f"llm{available_role_id}", "role_id": available_role_id})
            print(f"{room_id} join user: " + str({"user_id": f"llm{available_role_id}", "role_id": available_role_id}))
        await chatroom_collection.update_one(
            {"chatroom_id": room_id},
            {"$set": {"status": "start"}}
        )
        # await socket_manager.emit("chatroom_start", {"room_id": room_id}, to=room_id)

    return {"message": "User joined", "role_id": role_id, "code":0}


@socket_manager.on("check_in")
async def room_status(sid, data):
    room_id = data["room_id"]
    chatroom = await chatroom_collection.find_one({"chatroom_id": room_id})
    print("current_status" + str({"code": 0, "status": chatroom["status"]}))
    await socket_manager.enter_room(sid, room_id)
    await socket_manager.emit("current_status", {"code": 0, "status": chatroom["status"]}, to=room_id)
    if chatroom["status"] == 'start':
        first_player = next(user for user in chatroom["users"] if user["role_id"] == 1)
        print("first player: "+ str(first_player))
        if first_player["user_id"] == f"llm1":
            await call_llm_api(room_id, 1)

async def process_send_message(room_id: str, user_id: str, message: str, sid=''):
    # 查找聊天室
    chatroom = await chatroom_collection.find_one({"chatroom_id": room_id})
    if not chatroom or chatroom["status"] != "start":
        return {"error": "Chatroom is not active"}

    # 获取用户角色
    user = next((user for user in chatroom["users"] if user["user_id"] == user_id), None)
    if not user:
        return {"error": "User not found in chatroom"}
    role_id = user["role_id"]

    # 获取当前轮次
    room_messages = await room_messages_collection.find_one({"room_id": room_id})
    print("room_messages: " + str(room_messages))
    current_round = len(room_messages["messages"]) if room_messages else 1
    print("current_round: " + str(current_round))

    # 检查发送消息的顺序
    if room_messages:
        current_round_messages = room_messages["messages"][current_round-1] if current_round <= len(room_messages["messages"]) else []
        print("current_round_messages: " + str(current_round_messages))
        if len(current_round_messages) != role_id - 1:
            print("error, not your turn to send message")
            return {"error": "Not your turn to send message"}
        # if any(msg for msg in current_round_messages if list(msg.keys())[0] == f"role_{role_id}"):
        #     return {"error": "You have already sent a message in this round"}

    # 存储消息
    new_message = {f"role_{role_id}": message, "time": time.time()}
    if room_messages:
        await room_messages_collection.update_one(
            {"room_id": room_id},
            {"$push": {f"messages.{current_round-1}": new_message}}
        )
    else:
        await room_messages_collection.insert_one({
            "room_id": room_id,
            "messages": [[new_message]]
        })

    # 获取更新后的消息
    updated_messages = await room_messages_collection.find_one({"room_id": room_id})

    # 检查轮次是否结束
    updated_round_messages = updated_messages["messages"][current_round-1]

    response = {"message": "Message sent", "all_messages": updated_messages["messages"], "role_id": role_id,
                "last_messages": updated_messages["messages"][-1][-1]}
    if "error" in response:
        await socket_manager.emit("error", response["error"], to=sid)
        return

    # 广播消息给房间的所有用户
    print("-------------------------------ready to pull new message-----------------------------")
    sent_role_id = f'role_{role_id}'
    await socket_manager.emit("new_message", {
        "code": 0,
        "role_id": response["role_id"],
        "room_id": room_id,
        "last_messages": response["last_messages"][sent_role_id]
    }, to=room_id)


    if len(updated_round_messages) == len(chatroom["users"]):  # 所有用户发完消息
        if current_round == Max_Round:  # 达到最大轮次
            await chatroom_collection.update_one({"chatroom_id": room_id}, {"$set": {"status": "voting"}})
            await socket_manager.emit("current_status", {"code": 0, "status": 'voting'}, to=room_id)
            return
        else:
            await socket_manager.emit("next_round", {"round": current_round}, to=room_id)
            await room_messages_collection.update_one(
                {"room_id": room_id},
                {"$push": {"messages": []}}
            )

    # 检查下一个用户是否是llm
    next_role_id = role_id % 5 + 1
    print("next_role_id: " + str(next_role_id))
    next_user = next((user for user in chatroom["users"] if user["role_id"] == next_role_id), None)
    print("next_user: " +  str(next_user))


    if next_user["user_id"] == f"llm{next_role_id}":
        await call_llm_api(room_id, next_role_id)

    # return {"message": "Message sent", "all_messages": updated_messages["messages"], "role_id": role_id, "last_messages": updated_messages["messages"][-1][-1]}

async def call_llm_api(room_id: str, role_id:int):
    # 获取当前房间所有消息
    print("call llm: " + str(room_id) + " -role_id=" + str(role_id))
    room_messages = await room_messages_collection.find_one({"room_id": room_id})
    if (not room_messages) and role_id != 1:
        print("error: Room messages not found by call llm api")
        return {"error": "Room messages not found"}

    messages_to_send = []
    try:
        for round_messages in room_messages["messages"]:
            for message in round_messages:
                for role, msg in message.items():
                    if "role" in role:
                        messages_to_send.append({
                            "role": role,
                            "content": msg
                        })
    except TypeError:
        print("this is the first round")

    # LLM API 请求

    # messages_to_send.insert(0, {"role": "role_0", "content": "You are in a game named whoisllm. you should pretend to be a real human. Send a message and try not to be distinguished by other human player. You can choose topic such as 'self_introduction'/'popular video game, music or film' or any other topic. The nexts are other players' message."})

    print("message to gpt4:" + str(messages_to_send))
    llm_response = requests.post(
        f"http://{LLM_URL}:40013/v1/llm/chat",
        json={"messages": messages_to_send}
    )

    if llm_response.status_code == 200:
        # 假设 LLM API 返回结果并添加到房间消息中
        llm_message = llm_response.json().get("reply", "")
        await process_send_message(room_id, f"llm{role_id}", llm_message)
    else:
        print(f"LLM API call failed with status code {llm_response.status_code}")

@socket_manager.on("send_message")
async def send_message(sid, data):
    room_id = data["room_id"]
    user_id = data["user_id"]
    message = data["message"]

    await process_send_message(room_id, user_id, message, sid)


from fastapi import HTTPException

# @app.post("/v1/chatroom/send_message")
# async def send_message_http(room_id: str, user_id: str, message: str):
#     response = await process_send_message(room_id, user_id, message)
#     if "error" in response:
#         raise HTTPException(status_code=400, detail=response["error"])
#     return response

@socket_manager.on("send_vote")
async def vote(sid, data):
    room_id = data["room_id"]
    vote = data["vote"]
    user_id = data["user_id"]
    print(f'----------------------------------voting stage----------------------------------')
    print(f'{user_id} vote {vote} in {room_id}')
    chatroom = await chatroom_collection.find_one({"chatroom_id": room_id, "status": "voting"})
    if not chatroom:
        result = {'code': 1, 'message': 'room not found'}
        print(result)
        await socket_manager.emit('error', result, to=sid)
        return result


    user = next((user for user in chatroom["users"] if user["user_id"] == user_id), None)
    llms = [llm for llm in chatroom["users"] if llm["user_id"] == 'llm'+ str(llm['role_id'])]
    if not user:
        print({"error": "User not found in chatroom"})
        return {"error": "User not found in chatroom"}
    role_id = vote.split(",")
    score = 0
    for i in role_id:
        for llm in llms:
            if llm['role_id'] == int(i):
                score += 1
    await chatroom_collection.update_one(
        {"chatroom_id": room_id},
        {"$push": {"score": {"user_id": user_id, "score": score, "sid": sid}}}
    )
    chatroom["score"].append({"user_id": user_id, "score": score, "sid": sid})
    print(f"chatroom score {chatroom['score']}")
    if len(chatroom["score"]) == 3:
        sorted_scores = sorted(chatroom["score"], key=lambda x:x['score'], reverse=True)
        max_score = sorted_scores[0]['score']
        # max_items = [item for item in sorted_scores if item['score'] == max_score]
        for player in chatroom["score"]:
            print(f"send to {player['user_id']}, score {player['score']}")
            await socket_manager.emit("vote_status", {"code": 0, "score": player["score"], "isWinner": player["score"]==max_score}, to=player["sid"])
        await chatroom_collection.update_one({"chatroom_id": room_id}, {"$set": {"status": "end"}})


    # await socket_manager.emit("current_status", {"code": 0, "status": chatroom["status"]}, to=room_id)





if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
