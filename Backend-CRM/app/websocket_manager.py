from typing import Dict, Set, Optional
from fastapi import WebSocket
import json
from uuid import UUID
import redis.asyncio as aioredis
from app.config import settings
import asyncio


class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[UUID, Set[WebSocket]] = {}
        self.redis_client: Optional[aioredis.Redis] = None
        self.pubsub = None
        self._listening = False
        self.redis_disabled = False

    # -------------------------------------------------
    # WebSocket connection handling
    # -------------------------------------------------

    async def connect(self, websocket: WebSocket, conversation_id: UUID):
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = set()

        self.active_connections[conversation_id].add(websocket)

        # 🔥 IMPORTANT: Start heartbeat to prevent Azure idle disconnects
        asyncio.create_task(self._heartbeat(websocket))

    async def disconnect(self, websocket: WebSocket, conversation_id: UUID):
        if conversation_id in self.active_connections:
            self.active_connections[conversation_id].discard(websocket)
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending WebSocket message: {e}")

    async def broadcast_to_conversation(self, conversation_id: UUID, message: dict):
        if conversation_id not in self.active_connections:
            return

        disconnected = set()

        for connection in self.active_connections[conversation_id]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)

        for conn in disconnected:
            self.active_connections[conversation_id].discard(conn)

    # -------------------------------------------------
    # HEARTBEAT (CRITICAL FOR AZURE)
    # -------------------------------------------------

    async def _heartbeat(self, websocket: WebSocket):
        """
        Keeps WebSocket alive to avoid Azure 1006 idle disconnects.
        """
        try:
            while True:
                await asyncio.sleep(20)  # Azure-safe interval
                await websocket.send_json({"type": "ping"})
        except Exception:
            # Socket closed or client gone
            pass

    # -------------------------------------------------
    # Redis initialization
    # -------------------------------------------------

    async def init_redis(self):
        if self.redis_disabled:
            return

        if self.redis_client is not None:
            return

        try:
            redis_url = settings.redis_url

            if not redis_url:
                raise RuntimeError("redis_url not configured")

            self.redis_client = await asyncio.wait_for(
                aioredis.from_url(
                    redis_url,
                    decode_responses=False,
                    socket_connect_timeout=5,
                ),
                timeout=6.0,
            )

            await asyncio.wait_for(self.redis_client.ping(), timeout=3.0)

            self.pubsub = self.redis_client.pubsub()
            print("✅ Redis connected successfully for WebSocket pub/sub")

        except Exception as e:
            print(f"⚠️ Redis permanently disabled for this worker: {e}")
            self.redis_client = None
            self.pubsub = None
            self.redis_disabled = True

    # -------------------------------------------------
    # Redis listener
    # -------------------------------------------------

    async def start_listening(self):
        if self._listening or self.redis_disabled:
            return

        await self.init_redis()

        if self.redis_client is None or self.pubsub is None:
            print("Warning: Cannot start Redis listener - Redis not available")
            return

        self._listening = True
        asyncio.create_task(self._redis_listener())

    async def _redis_listener(self):
        if self.pubsub is None:
            return

        try:
            await self.pubsub.psubscribe("conversation.*")

            async for message in self.pubsub.listen():
                if message.get("type") != "pmessage":
                    continue

                try:
                    channel = message["channel"].decode()
                    conv_id_str = channel.split(".")[-1]
                    conversation_id = UUID(conv_id_str)
                    data = json.loads(message["data"].decode())

                    await self.broadcast_to_conversation(conversation_id, data)

                except Exception as e:
                    print(f"Error processing Redis message: {e}")

        except Exception as e:
            print(f"Redis listener crashed, disabling Redis: {e}")
            self.redis_disabled = True
            self.redis_client = None
            self.pubsub = None
            self._listening = False

    # -------------------------------------------------
    # Publishing events
    # -------------------------------------------------

    async def publish_event(self, conversation_id: UUID, event_data: dict):
        # Fallback to in-memory broadcast
        if self.redis_disabled:
            await self.broadcast_to_conversation(conversation_id, event_data)
            return

        if self.redis_client is None:
            await self.init_redis()

        if self.redis_client is None:
            self.redis_disabled = True
            await self.broadcast_to_conversation(conversation_id, event_data)
            return

        try:
            channel = f"conversation.{conversation_id}"
            await self.redis_client.publish(channel, json.dumps(event_data))
        except Exception as e:
            print(f"Redis publish failed, disabling Redis: {e}")
            self.redis_disabled = True
            await self.broadcast_to_conversation(conversation_id, event_data)

    async def publish_thread_update(self, thread_id: UUID, event_data: dict):
        if self.redis_disabled:
            return

        if self.redis_client is None:
            await self.init_redis()

        if self.redis_client is None:
            self.redis_disabled = True
            return

        try:
            channel = f"thread.{thread_id}"
            await self.redis_client.publish(channel, json.dumps(event_data))
        except Exception as e:
            print(f"Redis thread publish failed, disabling Redis: {e}")
            self.redis_disabled = True


# Singleton
manager = WebSocketManager()
