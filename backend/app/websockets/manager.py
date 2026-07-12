import json
import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Maps employee_id -> set of active WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # Keep map of connection -> employee_id to make disconnect cleanup fast
        self.connection_to_employee: Dict[WebSocket, int] = {}
        # Store connection -> department_id to easily support department broadcasts
        self.connection_to_department: Dict[WebSocket, int] = {}

    async def connect(self, websocket: WebSocket, employee_id: int, department_id: int):
        await websocket.accept()
        if employee_id not in self.active_connections:
            self.active_connections[employee_id] = set()
        self.active_connections[employee_id].add(websocket)
        self.connection_to_employee[websocket] = employee_id
        self.connection_to_department[websocket] = department_id
        logger.info(f"WebSocket connected for employee {employee_id} (dept {department_id})")

    def disconnect(self, websocket: WebSocket):
        employee_id = self.connection_to_employee.pop(websocket, None)
        self.connection_to_department.pop(websocket, None)
        if employee_id and employee_id in self.active_connections:
            self.active_connections[employee_id].discard(websocket)
            if not self.active_connections[employee_id]:
                del self.active_connections[employee_id]
        logger.info(f"WebSocket disconnected for employee {employee_id}")

    async def broadcast_to_employee(self, employee_id: int, payload: dict):
        """Sends payload to all active connections for a specific employee."""
        connections = self.active_connections.get(employee_id, set())
        if connections:
            message = json.dumps(payload)
            for connection in list(connections):
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Error sending to employee {employee_id} connection: {e}")
                    self.disconnect(connection)

    async def broadcast_to_department(self, department_id: int, payload: dict):
        """Sends payload to all connected employees belonging to a specific department."""
        message = json.dumps(payload)
        for connection, dept_id in list(self.connection_to_department.items()):
            if dept_id == department_id:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Error sending to department {department_id} connection: {e}")
                    self.disconnect(connection)

    async def broadcast_org_wide(self, payload: dict):
        """Sends payload to all active WebSocket connections across the entire organisation."""
        message = json.dumps(payload)
        for connection in list(self.connection_to_employee.keys()):
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error sending org-wide connection: {e}")
                self.disconnect(connection)

ws_manager = ConnectionManager()
