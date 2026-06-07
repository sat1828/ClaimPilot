import json
import logging
from typing import Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, adjuster_id: str, websocket: WebSocket):
        await websocket.accept()
        if adjuster_id not in self.active_connections:
            self.active_connections[adjuster_id] = []
        self.active_connections[adjuster_id].append(websocket)
        logger.info(f"Adjuster {adjuster_id} connected. Total connections: {len(self.active_connections[adjuster_id])}")

    def disconnect(self, adjuster_id: str, websocket: WebSocket):
        if adjuster_id in self.active_connections:
            self.active_connections[adjuster_id].remove(websocket)
            if not self.active_connections[adjuster_id]:
                del self.active_connections[adjuster_id]
            logger.info(f"Adjuster {adjuster_id} disconnected")

    async def send_to_adjuster(self, adjuster_id: str, message: dict):
        if adjuster_id in self.active_connections:
            dead_connections = []
            for ws in self.active_connections[adjuster_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead_connections.append(ws)
            for ws in dead_connections:
                self.active_connections[adjuster_id].remove(ws)

    async def broadcast(self, message: dict):
        for adjuster_id in list(self.active_connections.keys()):
            await self.send_to_adjuster(adjuster_id, message)

    async def send_escalation(self, adjuster_id: str, case_summary: dict):
        await self.send_to_adjuster(adjuster_id, {
            "type": "ESCALATION",
            "payload": case_summary,
        })


manager = ConnectionManager()


@router.websocket("/adjuster/{adjuster_id}")
async def adjuster_websocket(websocket: WebSocket, adjuster_id: str):
    await manager.connect(adjuster_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                msg_type = message.get("type", "")

                if msg_type == "DECISION":
                    logger.info(f"WebSocket decision from {adjuster_id}: {message.get('claim_id')} -> {message.get('decision')}")
                    await manager.send_to_adjuster(adjuster_id, {
                        "type": "DECISION_RECEIVED",
                        "claim_id": message.get("claim_id"),
                        "decision": message.get("decision"),
                        "status": "RECORDED",
                    })
                elif msg_type == "PING":
                    await websocket.send_json({"type": "PONG"})

            except json.JSONDecodeError:
                await websocket.send_json({"type": "ERROR", "message": "Invalid JSON"})

    except WebSocketDisconnect:
        manager.disconnect(adjuster_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error for {adjuster_id}: {e}")
        manager.disconnect(adjuster_id, websocket)
