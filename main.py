import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api import construction_works, users
from api.handlers import router

app = FastAPI(
    title="Справочник строительных работ",
    description=(
        "Сессионная аутентификация через куку sessionId, сессии хранятся в Redis. "
        "Без входа доступны только GET списка и ленты. "
        "Для методов создателя выполните POST /api/users/login: браузер сохранит куку и будет отправлять её сам."
    ),
)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(router)
app.include_router(construction_works.router)
app.include_router(users.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
