import redis.asyncio as aioredis
from app.core.config import settings
import logging

logger = logging.getLogger("raxus.redis")
redis_client = None


async def init_redis():
    global redis_client
    redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    await redis_client.ping()
    logger.info("Redis connection established")


def get_redis():
    return redis_client
