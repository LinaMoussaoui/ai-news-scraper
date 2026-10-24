"""
Event Broadcasting System
Handles real-time event streaming using Redis Pub/Sub
"""
import json
import logging
import asyncio
from typing import Dict, List, Callable, Any
from datetime import datetime
import os

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None

logger = logging.getLogger(__name__)


class EventBroadcaster:
    """Handles publishing and subscribing to real-time events via Redis"""
    
    def __init__(self, redis_url: str = None):
        """Initialize event broadcaster"""
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://redis:6379/0')
        self.redis = None
        self.pubsub = None
        self._subscribers: Dict[str, List[Callable]] = {}
        logger.info(f"EventBroadcaster initialized: {self.redis_url}")
    
    async def connect(self) -> bool:
        """Connect to Redis"""
        if not REDIS_AVAILABLE:
            logger.warning("⚠️ Redis module not available - event broadcasting disabled")
            return False
        
        try:
            self.redis = await aioredis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            logger.info("✅ Connected to Redis for event broadcasting")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()
            logger.info("Disconnected from Redis")
    
    async def publish_event(self, channel: str, event_type: str, data: Any):
        """Publish an event to a channel"""
        if not REDIS_AVAILABLE or not self.redis:
            logger.debug(f"Skipping event publication (Redis unavailable): {channel}/{event_type}")
            return False
        
        try:
            event = {
                "type": event_type,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "data": data
            }
            
            await self.redis.publish(channel, json.dumps(event))
            logger.debug(f"📢 Event published: {channel}/{event_type}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to publish event: {e}")
            return False
    
    async def subscribe(self, channel: str):
        """Subscribe to a channel"""
        if not REDIS_AVAILABLE or not self.redis:
            logger.warning(f"Cannot subscribe to {channel} - Redis unavailable")
            return None
        
        try:
            pubsub = self.redis.pubsub()
            await pubsub.subscribe(channel)
            logger.debug(f"📥 Subscribed to channel: {channel}")
            return pubsub
        except Exception as e:
            logger.error(f"❌ Failed to subscribe to channel: {e}")
            return None


# Global broadcaster instance
_broadcaster: EventBroadcaster = None


async def get_broadcaster() -> EventBroadcaster:
    """Get or create global broadcaster instance"""
    global _broadcaster
    if _broadcaster is None:
        _broadcaster = EventBroadcaster()
        await _broadcaster.connect()
    return _broadcaster


# Event Channel Names
CHANNEL_BRONZE = "articles:bronze"
CHANNEL_SILVER = "articles:silver"
CHANNEL_GOLD = "analytics:gold"
CHANNEL_PIPELINE = "pipeline:status"

# Event Types
EVENT_ARTICLE_ADDED = "article_added"
EVENT_ARTICLES_BATCH = "articles_batch"
EVENT_TRANSFORMATION_STARTED = "transformation_started"
EVENT_TRANSFORMATION_COMPLETE = "transformation_complete"
EVENT_ANALYTICS_GENERATED = "analytics_generated"
EVENT_PIPELINE_START = "pipeline_start"
EVENT_PIPELINE_COMPLETE = "pipeline_complete"
EVENT_PIPELINE_ERROR = "pipeline_error"


async def broadcast_bronze_event(event_type: str, data: Any):
    """Broadcast Bronze layer event"""
    if not REDIS_AVAILABLE:
        return
    broadcaster = await get_broadcaster()
    await broadcaster.publish_event(CHANNEL_BRONZE, event_type, data)


async def broadcast_silver_event(event_type: str, data: Any):
    """Broadcast Silver layer event"""
    if not REDIS_AVAILABLE:
        return
    broadcaster = await get_broadcaster()
    await broadcaster.publish_event(CHANNEL_SILVER, event_type, data)


async def broadcast_gold_event(event_type: str, data: Any):
    """Broadcast Gold layer event"""
    if not REDIS_AVAILABLE:
        return
    broadcaster = await get_broadcaster()
    await broadcaster.publish_event(CHANNEL_GOLD, event_type, data)


async def broadcast_pipeline_event(event_type: str, data: Any):
    """Broadcast Pipeline status event"""
    if not REDIS_AVAILABLE:
        return
    broadcaster = await get_broadcaster()
    await broadcaster.publish_event(CHANNEL_PIPELINE, event_type, data)
