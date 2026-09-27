import hashlib

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from models.user import User
from schemas.user import UserOut, UserRegister

router = APIRouter(prefix="/api/users")


@router.post("/register", response_model=UserOut, status_code=201)
async def register_user(data: UserRegister, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.user_login == data.user_login))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Такой логин уже занят")

    user = User(
        user_login=data.user_login,
        password_hash=hashlib.sha256(data.password.encode()).hexdigest(),
    )
    db.add(user)
    await db.commit()
    return UserOut(id=user.id, user_login=user.user_login)


@router.post("/login")
async def login_user():
    return {"message": "Аутентификация появится в ЛР4"}


@router.post("/logout")
async def logout_user():
    return {"message": "Деавторизация появится в ЛР4"}
