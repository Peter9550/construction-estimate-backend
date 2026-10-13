from fastapi import Depends, HTTPException, Request
from fastapi.security import APIKeyCookie
from sqlalchemy.ext.asyncio import AsyncSession

from core.session_store import get_session_user_id
from db.session import get_db
from models.user import User

SESSION_COOKIE = "sessionId"

session_cookie = APIKeyCookie(
    name=SESSION_COOKIE,
    scheme_name="sessionId",
    description="Кука сессии. Ставится методом POST /api/users/login",
    auto_error=False,
)


async def find_session_user(db: AsyncSession, session_id: str | None):
    if session_id is None:
        return None
    user_id = await get_session_user_id(session_id)
    if user_id is None:
        return None
    return await db.get(User, user_id)


async def get_optional_user(request: Request, db: AsyncSession = Depends(get_db)):
    return await find_session_user(db, request.cookies.get(SESSION_COOKIE))


async def get_current_user(
    session_id: str | None = Depends(session_cookie),
    db: AsyncSession = Depends(get_db),
):
    user = await find_session_user(db, session_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Нужно войти в систему")
    return user
