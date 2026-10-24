"""
Real-Time WebSocket Endpoints
Streams live article and analytics events to connected clients
"""
import logging
import json
from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio

from backend.utils.event_broadcaster import (
    get_broadcaster,
    CHANNEL_BRONZE, CHANNEL_SILVER, CHANNEL_GOLD, CHANNEL_PIPELINE
)
from backend.utils.event_broadcaster import REDIS_AVAILABLE
from backend.utils.api_errors import ApiErrorPayload

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/realtime", tags=["realtime"])

# Check Redis availability
if not REDIS_AVAILABLE:
    logger.warning("⚠️ Redis not available - WebSocket endpoints will be limited")


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"✅ WebSocket connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"❌ WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send message to client: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected connections
        for conn in disconnected:
            self.active_connections.discard(conn)


manager = ConnectionManager()


async def _close_unavailable(websocket: WebSocket, error_code: str, error_message: str, suggested_fix: str):
    await websocket.accept()
    await websocket.send_json(
        ApiErrorPayload(
            error_code=error_code,
            error_message=error_message,
            suggested_fix=suggested_fix,
        ).to_dict()
    )
    await websocket.close(code=1011)


async def _relay_pubsub(websocket: WebSocket, pubsub, channel_name: str):
    async for message in pubsub.listen():
        if message['type'] == 'message':
            try:
                data = json.loads(message['data'])
                await websocket.send_json(data)
            except Exception as e:
                logger.error(f"Failed to relay {channel_name} message: {e}")


async def _listen_client(websocket: WebSocket):
    while True:
        try:
            data = await websocket.receive_json()
            if data.get('cmd') == 'ping':
                await websocket.send_json({"type": "pong"})
        except WebSocketDisconnect:
            break


@router.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    """
    WebSocket endpoint for real-time event streaming.
    Streams events from Bronze, Silver, Gold, and Pipeline channels.
    
    Usage:
        const ws = new WebSocket('ws://localhost:8000/realtime/ws/events');
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Event:', data);
        };
    """
    if not REDIS_AVAILABLE:
        await _close_unavailable(
            websocket,
            "REDIS_UNAVAILABLE",
            "Real-time event streaming is unavailable",
            "Install the redis Python package in the backend image and ensure the Redis service is healthy.",
        )
        return

    await manager.connect(websocket)
    broadcaster = await get_broadcaster()
    
    # Subscribe to all event channels
    try:
        # Create subscriptions for all channels
        pubsub_bronze = await broadcaster.subscribe(CHANNEL_BRONZE)
        pubsub_silver = await broadcaster.subscribe(CHANNEL_SILVER)
        pubsub_gold = await broadcaster.subscribe(CHANNEL_GOLD)
        pubsub_pipeline = await broadcaster.subscribe(CHANNEL_PIPELINE)
        
        pubsubs = [pubsub_bronze, pubsub_silver, pubsub_gold, pubsub_pipeline]

        if any(pubsub is None for pubsub in pubsubs):
            await websocket.send_json(
                ApiErrorPayload(
                    error_code="REDIS_SUBSCRIPTION_FAILED",
                    error_message="Unable to subscribe to one or more realtime channels",
                    suggested_fix="Check the Redis connection and restart the backend after installing the redis client package.",
                    details={"channels": [CHANNEL_BRONZE, CHANNEL_SILVER, CHANNEL_GOLD, CHANNEL_PIPELINE]},
                ).to_dict()
            )
            await websocket.close(code=1011)
            return
        
        relay_tasks = [
            asyncio.create_task(_relay_pubsub(websocket, pubsub_bronze, CHANNEL_BRONZE)),
            asyncio.create_task(_relay_pubsub(websocket, pubsub_silver, CHANNEL_SILVER)),
            asyncio.create_task(_relay_pubsub(websocket, pubsub_gold, CHANNEL_GOLD)),
            asyncio.create_task(_relay_pubsub(websocket, pubsub_pipeline, CHANNEL_PIPELINE)),
            asyncio.create_task(_listen_client(websocket)),
        ]

        done, pending = await asyncio.wait(relay_tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        for task in done:
            task.result()
        
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)
        # Cleanup pubsubs
        for pubsub in [pubsub_bronze, pubsub_silver, pubsub_gold, pubsub_pipeline]:
            if pubsub:
                await pubsub.unsubscribe()
                await pubsub.close()


@router.websocket("/ws/bronze")
async def websocket_bronze(websocket: WebSocket):
    """WebSocket endpoint for Bronze layer events only"""
    if not REDIS_AVAILABLE:
        await _close_unavailable(
            websocket,
            "REDIS_UNAVAILABLE",
            "Real-time event streaming is unavailable",
            "Install the redis Python package in the backend image and ensure the Redis service is healthy.",
        )
        return

    await manager.connect(websocket)
    broadcaster = await get_broadcaster()
    
    try:
        pubsub = await broadcaster.subscribe(CHANNEL_BRONZE)
        if pubsub is None:
            await websocket.send_json(
                ApiErrorPayload(
                    error_code="REDIS_SUBSCRIPTION_FAILED",
                    error_message="Unable to subscribe to the Bronze event channel",
                    suggested_fix="Check Redis connectivity and restart the backend.",
                ).to_dict()
            )
            await websocket.close(code=1011)
            return
        
        await asyncio.gather(
            _relay_pubsub(websocket, pubsub, CHANNEL_BRONZE),
            _listen_client(websocket),
        )
        
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)
        if pubsub:
            await pubsub.unsubscribe()
            await pubsub.close()


@router.websocket("/ws/silver")
async def websocket_silver(websocket: WebSocket):
    """WebSocket endpoint for Silver layer events only"""
    if not REDIS_AVAILABLE:
        await _close_unavailable(
            websocket,
            "REDIS_UNAVAILABLE",
            "Real-time event streaming is unavailable",
            "Install the redis Python package in the backend image and ensure the Redis service is healthy.",
        )
        return

    await manager.connect(websocket)
    broadcaster = await get_broadcaster()
    
    try:
        pubsub = await broadcaster.subscribe(CHANNEL_SILVER)
        if pubsub is None:
            await websocket.send_json(
                ApiErrorPayload(
                    error_code="REDIS_SUBSCRIPTION_FAILED",
                    error_message="Unable to subscribe to the Silver event channel",
                    suggested_fix="Check Redis connectivity and restart the backend.",
                ).to_dict()
            )
            await websocket.close(code=1011)
            return
        
        await asyncio.gather(
            _relay_pubsub(websocket, pubsub, CHANNEL_SILVER),
            _listen_client(websocket),
        )
        
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)
        if pubsub:
            await pubsub.unsubscribe()
            await pubsub.close()


@router.websocket("/ws/gold")
async def websocket_gold(websocket: WebSocket):
    """WebSocket endpoint for Gold layer events only"""
    if not REDIS_AVAILABLE:
        await _close_unavailable(
            websocket,
            "REDIS_UNAVAILABLE",
            "Real-time event streaming is unavailable",
            "Install the redis Python package in the backend image and ensure the Redis service is healthy.",
        )
        return

    await manager.connect(websocket)
    broadcaster = await get_broadcaster()
    
    try:
        pubsub = await broadcaster.subscribe(CHANNEL_GOLD)
        if pubsub is None:
            await websocket.send_json(
                ApiErrorPayload(
                    error_code="REDIS_SUBSCRIPTION_FAILED",
                    error_message="Unable to subscribe to the Gold event channel",
                    suggested_fix="Check Redis connectivity and restart the backend.",
                ).to_dict()
            )
            await websocket.close(code=1011)
            return
        
        await asyncio.gather(
            _relay_pubsub(websocket, pubsub, CHANNEL_GOLD),
            _listen_client(websocket),
        )
        
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)
        if pubsub:
            await pubsub.unsubscribe()
            await pubsub.close()
