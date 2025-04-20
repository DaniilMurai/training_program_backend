from redis.asyncio import Redis

class RedisClient:
    def __init__(self):
        self.client = Redis.from_url("redis://localhost:6379")

    async def setex(self, key: str, ttl: int, value: str):
        return await self.client.setex(key, ttl, value)

    async def get(self, key: str):
        return await self.client.get(key)

    async def delete(self, key: str):
        return await self.client.delete(key)

