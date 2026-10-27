from redis.asyncio import Redis

from core.config import settings

SESSION_TTL_SECONDS = 3600

redis_client = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)


def session_key(session_id):
    return f"session:{session_id}"


async def create_session(session_id, user):
    key = session_key(session_id)
    await redis_client.hset(key, mapping={"user_id": user.id, "user_login": user.user_login})
    await redis_client.expire(key, SESSION_TTL_SECONDS)


async def get_session_user_id(session_id):
    user_id = await redis_client.hget(session_key(session_id), "user_id")
    return int(user_id) if user_id else None


async def destroy_session(session_id):
    await redis_client.delete(session_key(session_id))
