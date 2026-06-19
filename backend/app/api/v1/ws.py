from __future__ import annotations

import json
import uuid
from collections import defaultdict
from typing import Any

import jwt
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.security import decode_token

router = APIRouter()

# Connection pool: {trip_id: {user_id: websocket}}
_connections: dict[uuid.UUID, dict[uuid.UUID, WebSocket]] = defaultdict(dict)


def _validate_token(token: str | None) -> uuid.UUID | None:
    """Validate the WebSocket token and return the user_id, or None on failure."""
    if not token:
        return None
    try:
        payload = decode_token(token)
    except jwt.PyJWTError:
        return None

    if payload.get("type") != "access":
        return None

    user_id_raw = payload.get("sub")
    if not user_id_raw:
        return None

    try:
        return uuid.UUID(user_id_raw)
    except (ValueError, AttributeError):
        return None


async def _broadcast(
    trip_id: uuid.UUID,
    message: dict[str, Any],
    exclude_user: uuid.UUID | None = None,
) -> None:
    """Broadcast a message to all connected users in a trip."""
    users = _connections.get(trip_id, {})
    if not users:
        return
    message_str = json.dumps(message, ensure_ascii=False)
    disconnected: list[uuid.UUID] = []
    for uid, ws in users.items():
        if exclude_user is not None and uid == exclude_user:
            continue
        try:
            await ws.send_text(message_str)
        except Exception:
            disconnected.append(uid)

    for uid in disconnected:
        _connections.get(trip_id, {}).pop(uid, None)


async def _send_presence(trip_id: uuid.UUID, websocket: WebSocket) -> None:
    """Send current online users to a newly connected user."""
    users = _connections.get(trip_id, {})
    online_users = [str(uid) for uid in users.keys()]
    message = json.dumps(
        {
            "type": "presence",
            "online_users": online_users,
            "trip_id": str(trip_id),
        },
        ensure_ascii=False,
    )
    try:
        await websocket.send_text(message)
    except Exception:
        pass


def _remove_connection(trip_id: uuid.UUID, user_id: uuid.UUID) -> None:
    """Remove a user's connection from the pool."""
    trip_pool = _connections.get(trip_id)
    if trip_pool is not None:
        trip_pool.pop(user_id, None)
        if not trip_pool:
            _connections.pop(trip_id, None)


@router.websocket("/ws/trips/{trip_id}", name="trip_collaboration")
async def trip_collaboration_ws(
    websocket: WebSocket,
    trip_id: uuid.UUID,
    token: str | None = Query(default=None),
) -> None:
    """协同编辑 WebSocket 端点。

    通过 query 参数 ?token=xxx 验证用户身份，维护每个 trip 的连接池，
    支持光标移动、模块锁定/解锁、编辑操作、在线状态等消息类型。
    """
    user_id = _validate_token(token)
    if user_id is None:
        await websocket.close(code=4001, reason="无效的认证凭据")
        return

    await websocket.accept()
    _connections[trip_id][user_id] = websocket

    # Broadcast user_joined to other users
    await _broadcast(
        trip_id,
        {
            "type": "user_joined",
            "user_id": str(user_id),
            "trip_id": str(trip_id),
        },
        exclude_user=user_id,
    )

    # Send current presence to the new user
    await _send_presence(trip_id, websocket)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                message = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                continue

            msg_type = message.get("type")
            if msg_type == "cursor_move":
                await _broadcast(
                    trip_id,
                    {
                        "type": "cursor_move",
                        "user_id": str(user_id),
                        "data": message.get("data", {}),
                    },
                    exclude_user=user_id,
                )
            elif msg_type == "module_lock":
                await _broadcast(
                    trip_id,
                    {
                        "type": "module_lock",
                        "user_id": str(user_id),
                        "module": message.get("module"),
                        "data": message.get("data", {}),
                    },
                    exclude_user=user_id,
                )
            elif msg_type == "module_unlock":
                await _broadcast(
                    trip_id,
                    {
                        "type": "module_unlock",
                        "user_id": str(user_id),
                        "module": message.get("module"),
                    },
                    exclude_user=user_id,
                )
            elif msg_type == "edit":
                await _broadcast(
                    trip_id,
                    {
                        "type": "edit",
                        "user_id": str(user_id),
                        "module": message.get("module"),
                        "data": message.get("data", {}),
                    },
                    exclude_user=user_id,
                )
            elif msg_type == "presence":
                await _broadcast(
                    trip_id,
                    {
                        "type": "presence",
                        "user_id": str(user_id),
                        "status": message.get("status", "online"),
                    },
                    exclude_user=user_id,
                )
    except WebSocketDisconnect:
        pass
    finally:
        _remove_connection(trip_id, user_id)
        await _broadcast(
            trip_id,
            {
                "type": "user_left",
                "user_id": str(user_id),
                "trip_id": str(trip_id),
            },
        )
