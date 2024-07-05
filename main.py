from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict

app = FastAPI()

# Allow all origins (adjust as needed)
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


class User(BaseModel):
    username: str


class Room(BaseModel):
    room_id: str
    users: List[User] = []
    messages: List[str] = []


# In-memory storage for rooms
rooms: Dict[str, Room] = {}


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, room_id: str, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, room_id: str, websocket: WebSocket):
        self.active_connections[room_id].remove(websocket)
        if not self.active_connections[room_id]:
            del self.active_connections[room_id]

    async def send_message(self, room_id: str, message: str):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_text(message)
                except RuntimeError as e:
                    print(f"Error sending message: {e}")
                    self.disconnect(room_id, connection)


manager = ConnectionManager()


@app.post("/create_room/")
async def create_room(room_id: str):
    if room_id in rooms:
        return {"error": "Room already exists"}
    rooms[room_id] = Room(room_id=room_id)
    return {"message": "Room created", "room_id": room_id}


@app.post("/join_room/")
async def join_room(room_id: str, user: User):
    if room_id not in rooms:
        return {"error": "Room not found"}
    rooms[room_id].users.append(user)
    return {"message": f"{user.username} joined room {room_id}"}


@app.websocket("/ws/{room_id}/{username}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, username: str):
    if room_id not in rooms:
        await websocket.close(code=404)
        return

    await manager.connect(room_id, websocket)
    await manager.send_message(room_id, f"{username} has joined the chat")

    try:
        while True:
            data = await websocket.receive_text()
            message = f"{username}: {data}"
            rooms[room_id].messages.append(message)
            await manager.send_message(room_id, message)
    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)
        await manager.send_message(room_id, f"{username} has left the chat")


@app.get("/")
async def get():
    return FileResponse("index.html")


@app.get("/api/check_room/{room_id}")
async def check_room(room_id: str):
    return {"exists": room_id in rooms}


# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run(app, host="127.0.0.1", port=8000)
