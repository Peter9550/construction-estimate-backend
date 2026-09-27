from pydantic import BaseModel, ConfigDict, Field


class UserRegister(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_login: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=100)


class UserOut(BaseModel):
    id: int
    user_login: str
