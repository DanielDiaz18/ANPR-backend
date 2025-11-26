from typing import List, Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
import json
from datetime import datetime


class ConnectionManager:
    """Manager for WebSocket connections"""
    
    def __init__(self):
        # Store active connections by topic
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "services": set(),
            "vehicles": set(),
            "clients": set(),
            "all": set()
        }
    
    async def connect(self, websocket: WebSocket, topic: str = "all"):
        """Connect a WebSocket client to a specific topic"""
        await websocket.accept()
        if topic not in self.active_connections:
            self.active_connections[topic] = set()
        self.active_connections[topic].add(websocket)
        self.active_connections["all"].add(websocket)
    
    def disconnect(self, websocket: WebSocket, topic: str = "all"):
        """Disconnect a WebSocket client from a specific topic"""
        if topic in self.active_connections:
            self.active_connections[topic].discard(websocket)
        self.active_connections["all"].discard(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket client"""
        await websocket.send_text(message)
    
    async def broadcast_to_topic(self, message: dict, topic: str = "all"):
        """Broadcast a message to all clients subscribed to a topic"""
        message_str = json.dumps({
            **message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        connections = self.active_connections.get(topic, set()).copy()
        disconnected = set()
        
        for connection in connections:
            try:
                await connection.send_text(message_str)
            except Exception:
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection, topic)
    
    async def broadcast_service_update(self, action: str, service_data: dict):
        """Broadcast service updates to all subscribed clients"""
        message = {
            "type": "update",
            "action": action,  # create, update, delete
            "data": service_data
        }
        await self.broadcast_to_topic(message, "services")
        await self.broadcast_to_topic(message, "all")

    async def broadcast_client_update(self, action: str, client_data: dict):
        """Broadcast client updates to all subscribed clients"""
        message = {
            "type": "update",
            "action": action,  # create, update, delete
            "data": client_data
        }
        await self.broadcast_to_topic(message, "clients")
        await self.broadcast_to_topic(message, "all")
    
    async def broadcast_vehicle_update(self, action: str, vehicle_data: dict):
        """Broadcast vehicle updates to all subscribed clients"""
        message = {
            "type": "update",
            "action": action,  # create, update, delete
            "data": vehicle_data
        }
        await self.broadcast_to_topic(message, "vehicles")
        await self.broadcast_to_topic(message, "all")
    
    def get_active_connections_count(self, topic: str = "all") -> int:
        """Get the number of active connections for a topic"""
        return len(self.active_connections.get(topic, set()))


# Global instance
manager = ConnectionManager()
