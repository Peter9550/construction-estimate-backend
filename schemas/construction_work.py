from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConstructionWorkOut(BaseModel):
    id: int
    work_name: str
    work_description: str | None
    work_status: str
    image_url: str | None
    video_url: str | None
    historical_price: int | None
    base_year: int | None
    created_at: datetime
    formed_at: datetime | None
    likes_count: int
    is_mine: int
    is_liked: int


class ConstructionWorkPublish(BaseModel):
    model_config = ConfigDict(extra="forbid")

    work_description: str = Field(min_length=1, max_length=500)
    historical_price: int = Field(gt=0)
    base_year: int = Field(ge=1000, le=2100)


class WorkLikeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    like: int = Field(ge=0, le=1)
