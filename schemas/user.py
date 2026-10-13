from pydantic import BaseModel, ConfigDict, Field


class UserRegister(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_login: str = Field(min_length=3, max_length=50, examples=["ivanov"])
    password: str = Field(min_length=6, max_length=100, examples=["secret123"])


class UserLogin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_login: str = Field(examples=["petrov"])
    password: str = Field(examples=["password123"])


class UserOut(BaseModel):
    id: int
    user_login: str
