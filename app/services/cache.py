import redis.asyncio as redis
from typing import Optional
import json

class CacheService:
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.client: Optional[redis.Redis] = None
    
    async def connect(self):
        self.client = await redis.from_url(self.redis_url, decode_responses=True)
    
    async def close(self):
        if self.client:
            await self.client.close()
    
    async def get(self, key: str) -> Optional[str]:
        if not self.client:
            return None
        try:
            return await self.client.get(key)
        except Exception:
            return None
    
    async def set(self, key: str, value: str, ttl: int = 900):
        """Set cache with TTL (default 15 minutes)"""
        if not self.client:
            return
        try:
            await self.client.setex(key, ttl, value)
        except Exception:
            pass
    
    async def get_stats(self, username: str) -> Optional[dict]:
        data = await self.get(f"stats:{username}")
        if data:
            return json.loads(data)
        return None
    
    async def set_stats(self, username: str, stats: dict, ttl: int = 900):
        await self.set(f"stats:{username}", json.dumps(stats), ttl)
