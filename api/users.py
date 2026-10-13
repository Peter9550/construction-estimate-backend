import hashlib
import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.current_user import SESSION_COOKIE, session_cookie
from core.session_store import SESSION_TTL_SECONDS, create_session, destroy_session
from db.session import get_db
from models.user import User
from schemas.user import UserLogin, UserOut, UserRegister

router = APIRouter(prefix="/api/users", tags=["Пользователи"])


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


@router.post(
    "/register",
    response_model=UserOut,
    status_code=201,
    summary="Регистрация",
    description="Создаёт пользователя. Пароль хранится как хеш SHA-256. 409 - логин занят.",
)
async def register_user(data: UserRegister, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.user_login == data.user_login))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Такой логин уже занят")

    user = User(user_login=data.user_login, password_hash=hash_password(data.password))
    db.add(user)
    await db.commit()
    return UserOut(id=user.id, user_login=user.user_login)


@router.post(
    "/login",
    response_model=UserOut,
    summary="Аутентификация",
    description=(
        "Проверяет логин и пароль, создаёт сессию в Redis на 1 час и ставит куку sessionId (HttpOnly). "
        "Дальше браузер сам отправляет куку в каждом запросе. 401 - неверный логин или пароль."
    ),
)
async def login_user(data: UserLogin, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.user_login == data.user_login))
    user = result.scalar_one_or_none()
    if user is None or user.password_hash != hash_password(data.password):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    session_id = str(uuid.uuid4())
    await create_session(session_id, user.id)
    response.set_cookie(
        SESSION_COOKIE,
        session_id,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        secure=False,
    )
    return UserOut(id=user.id, user_login=user.user_login)


@router.post(
    "/logout",
    summary="Деавторизация",
    description="Удаляет сессию из Redis и куку sessionId. После этого кука больше не действует.",
)
async def logout_user(response: Response, session_id: str | None = Depends(session_cookie)):
    if session_id is not None:
        await destroy_session(session_id)
    response.delete_cookie(SESSION_COOKIE)
    return {"message": "Сессия завершена"}
