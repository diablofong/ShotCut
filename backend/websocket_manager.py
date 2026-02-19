import json
from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self._connections: dict[int, set[WebSocket]] = defaultdict(set)

    async def connect(self, video_id: int, websocket: WebSocket):
        await websocket.accept()
        self._connections[video_id].add(websocket)

    def disconnect(self, video_id: int, websocket: WebSocket):
        self._connections[video_id].discard(websocket)
        if not self._connections[video_id]:
            del self._connections[video_id]

    async def broadcast(self, video_id: int, data: dict):
        if video_id not in self._connections:
            return
        dead = set()
        for ws in self._connections[video_id]:
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.disconnect(video_id, ws)


manager = ConnectionManager()
