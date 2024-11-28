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


@sio.on("user_joined")
def user_joined(data):
    print("User joined room:", data)


@sio.on("new_message")
def new_message(data):
    print("New message received:", data)

if __name__ == '__main__':
    # 用户名：444@qq.com
    user_id = "444@qq.com"
    role_id = 3

    sio.connect(SERVER_URL, socketio_path='/socket.io/')

    # # 创建房间 (通过 HTTP)
    # create_room("room_1", "creator_123")

    # # 加入房间 (通过 Socket.IO)
    join_room("room_8726", "user_kkk")

    # # 发送消息 (通过 Socket.IO)
    # send_message("room_8106", "user_456", "Hello, this is a test message!")

    # 运行直到手动中止
    sio.wait()