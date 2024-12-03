from test_sender import *

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


@sio.on("new_message")
def new_message(data):
    print("New message received:", data)

@sio.on("vote_status")
def vote_result(data):
    print(f"vote result: {data}")

@sio.on("current_status")
def current_status(data):
    print(f"chatroom status:{data}")

@sio.on("start_voting")
def start_vote(data):
    print(f"current stage: {data}")

if __name__ == '__main__':
    # 用户名：222@qq.com
    user_id = "333@qq.com"
    # 需要修改当前的roomid
    chatroom_id = 'room_5054'
    sio.connect(SERVER_URL, socketio_path='/socket.io/')

    # # 创建房间 (通过 HTTP)
    # create_room("room_1", user_id)

    # # 加入房间 (通过 Socket.IO)
    result = join_room(chatroom_id, user_id)
    check_in(chatroom_id)

    # # 发送消息 (通过 Socket.IO)
    # send_message(chatroom_id, user_id, "Hello, this is a test message!")
    while True:
        message = input("输入消息\n")
        if message == '1':
            send_message(chatroom_id, user_id, "Hello, this is a test message!")
        else:
            vote(chatroom_id, user_id=user_id, vote='1,5')

