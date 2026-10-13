from redis.asyncio import Redis

from core.config import settings

SESSION_TTL_SECONDS = 3600

redis_client = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)


def session_key(session_id):
    return f"session:{session_id}"


async def create_session(session_id, user_id):
    await redis_client.setex(session_key(session_id), SESSION_TTL_SECONDS, str(user_id))


async def get_session_user_id(session_id):
    user_id = await redis_client.get(session_key(session_id))
    return int(user_id) if user_id else None


async def destroy_session(session_id):
    await redis_client.delete(session_key(session_id))
