from fastapi import FastAPI

app = FastAPI()

@app.get("/chatroom/list")
async def chatroom_list():
    pass

@app.post("/chatroom/create")
async def chatroom_create():
    pass

@app.post("/chatroom/join")
async def chatroom_join():
    pass

