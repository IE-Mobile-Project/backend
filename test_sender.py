import socketio
import requests

# 后端地址
# SERVER_URL = "http://10.13.234.227:8000"
SERVER_URL = "http://10.13.130.55:8000"
sio = socketio.Client()

# Socket.IO 事件
@sio.event
def connect():
    print("Connected to server")


@sio.event
def connect_error(data):
    print("Failed to connect to server:", data)


@sio.event
def disconnect():
    print("Disconnected from server")


@sio.on("user_joined")
def user_joined(data):
    print("User joined room:", data)


@sio.on("new_message")
def new_message(data):
    print("New message received:", data)

@sio.on("chatroom_start")
def chatoom_start(data):
    print(f"chatroom start:{data}")


# 测试函数：创建房间
def create_room(chatroom_name, creator_id):
    url = f"{SERVER_URL}/v1/chatroom/create"
    params = {"chatroom_name": chatroom_name, "creator_id": creator_id}
    headers = {"content-type": 'application/json'}
    response = requests.post(url, json=params, headers=headers)
    print("Create Room Response:", response.json())
    return response.json()

def join_room(room_id, user_id):
    url = f"{SERVER_URL}/v1/chatroom/join"
    params = {"room_id": room_id, "user_id": user_id}
    headers = {"content-type": 'application/json'}
    response = requests.post(url, json=params, headers=headers)
    print("Join Room Response:", response.json())
    return response


# 测试函数：发送消息
def send_message(room_id, user_id, message):
    sio.emit("send_message", {"room_id": room_id, "user_id": user_id, "message": message})
    print(f"User {user_id} sent message to room {room_id}: {message}")

def vote(room_id, vote, user_id):
    sio.emit("send_vote", {"room_id":room_id, "user_id":user_id, "vote":vote})
    print(f"Vote {vote} to {room_id} from {user_id}")

@sio.on("vote_status")
def vote_result(data):
    print(f"vote result: {data}")

@sio.on("start_voting")
def start_vote(data):
    print(f"current stage: {data}")


def check_in(room_id):
    sio.emit("check_in", {"room_id": room_id})
    print(f"check in {room_id}")

@sio.on("current_status")
def current_status(data):
    print(f"chatroom status:{data}")


# 主测试逻辑
if __name__ == "__main__":
    #用户名：111@qq.com

    user_id = "111@qq.com"

    # 连接服务器
    sio.connect(SERVER_URL, socketio_path='/socket.io/')

    # 创建房间 (通过 HTTP)
    # 获取room_id和role_id

    result = create_room('Done', user_id)
    chatroom_id = result["chatroom_id"]
    role_id = result["role_id"]
    check_in(chatroom_id)

    # # 加入房间 (通过 Socket.IO)
    # join_room(chatroom_id, user_id)

    # # 发送消息 (通过 Socket.IO)
    # send_message(chatroom_id, user_id, "Hello, this is a test message!")

    # 运行直到手动中止
    while True:
        message = input("输入消息\n")
        if message == '1':
            send_message(chatroom_id, user_id, "Hello, this is a test message!")
        else:
            vote(chatroom_id, user_id=user_id, vote='1,2')