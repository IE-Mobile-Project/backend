chatroom_status = ["waiting", "start", "end"]
chatroom = {
    "chatroom_id":int,
    "chatroom_name":"",
    "status": "",
    "users":[{"user_id1": "", "role_id1": ""},{"user_id2": "", "role_id2": ""}, {"user_id3": "", "role_id3": ""}],
    # "llms" :[{"llm_id1":"", "role_id1": ""}]
}

messages = {
    "room_id": "room_1",
    "user_id": "user_123",
    "message": "Hello, world!",
    "timestamp": "2024-11-18T12:00:00"
}

room_messages = {
    "room_id": "",
    "messages":[
        [{"role_1": "message1"}, {"role_2": "message2"}, {"role3": "message10"}],
        [{"role_1": "message1"}, {"role_2": "message2"}, {"role3": "message10"}],
        [{"role_1": "message1"}, {"role_2": "message2"}, {"role3": "message10"}],
        [{"role_1": "message1"}, {"role_2": "message2"}, {"role3": "message10"}],
        [{"role_1": "message1"}, {"role_2": "message2"}, {"role3": "message10"}]
    ]
}