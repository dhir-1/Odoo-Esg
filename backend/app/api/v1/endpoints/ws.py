import json
import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from jose import jwt, JWTError
from sqlalchemy import select

from app.core.config import settings
from app.db.database import async_session_maker
from app.models.employee import Employee
from app.websockets.manager import ws_manager

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_websocket_user(token: str) -> Optional[Employee]:
    """
    Decodes the query parameter JWT token and returns the authenticated active Employee.
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: int = payload.get("user_id")
        if user_id is None:
            return None
    except JWTError:
        return None

    async with async_session_maker() as db:
        result = await db.execute(select(Employee).filter(Employee.id == user_id))
        user = result.scalars().first()
        if user and user.status.value == "Active":
            return user
    return None

@router.websocket("/live")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token passed as a query parameter")
):
    """
    WebSocket endpoint for real-time live events.
    Authenticates connection upgrade using the token query parameter.
    
    Why token in Query Parameter?
    Native browser WebSocket Client APIs do not support setting custom HTTP headers.
    Authenticating during the upgrade handshake allows the server to immediately reject
    unauthorized connections (returning 1008 Policy Violation) rather than accepting
    arbitrary TCP streams.
    """
    user = await get_websocket_user(token)
    if not user:
        logger.warning("Unauthenticated WebSocket upgrade request rejected.")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await ws_manager.connect(websocket, user.id, user.department_id)
    try:
        while True:
            # Keep socket alive and handle client input (e.g. ping message)
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except Exception:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
