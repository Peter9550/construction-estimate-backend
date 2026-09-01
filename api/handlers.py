from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates

from data.collections import (
    MINIO_BASE_URL,
    STATUS_DRAFT,
    STATUS_PUBLISHED,
    craft_resources,
)

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def published_resources():
    return [r for r in craft_resources if r["resource_status"] == STATUS_PUBLISHED]


def with_likes_count(resource):
    card = dict(resource)
    card["likes_count"] = len(resource["liked_by"])
    return card


@router.get("/craft-resources")
def get_craft_resource_catalog(request: Request, maxHistoricalPrice: str = ""):
    price_filter = maxHistoricalPrice.strip()
    resources = published_resources()

    if price_filter.isdigit():
        limit = int(price_filter)
        resources = [r for r in resources if r["historical_price"] <= limit]

    cards = [with_likes_count(r) for r in resources]

    return templates.TemplateResponse(
        request=request,
        name="catalog.html",
        context={
            "craft_resources": cards,
            "price_filter": price_filter,
            "active_tab": "catalog",
            "minio_base_url": MINIO_BASE_URL,
        },
    )


@router.get("/craft-resources/draft")
def get_craft_resource_draft(request: Request):
    for resource in craft_resources:
        if resource["resource_status"] == STATUS_DRAFT:
            return templates.TemplateResponse(
                request=request,
                name="draft.html",
                context={
                    "craft_resource": with_likes_count(resource),
                    "active_tab": "draft",
                    "minio_base_url": MINIO_BASE_URL,
                },
            )
    raise HTTPException(status_code=404, detail="Черновик не найден")


@router.get("/craft-resources/feed")
@router.get("/craft-resources/feed/{resource_id}")
def get_craft_resource_feed(request: Request, resource_id: int = 0, next: bool = False):
    resources = published_resources()
    if not resources:
        raise HTTPException(status_code=404, detail="Опубликованных ресурсов нет")

    position = 0
    if resource_id:
        position = None
        for index, resource in enumerate(resources):
            if resource["id"] == resource_id:
                position = index
                break
        if position is None:
            raise HTTPException(status_code=404, detail="Ресурс не найден")
        if next:
            position = (position + 1) % len(resources)

    current = resources[position]
    following = resources[(position + 1) % len(resources)]

    return templates.TemplateResponse(
        request=request,
        name="feed.html",
        context={
            "craft_resource": with_likes_count(current),
            "following_id": following["id"],
            "active_tab": "feed",
            "minio_base_url": MINIO_BASE_URL,
        },
    )
