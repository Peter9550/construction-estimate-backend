from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates

from data.collections import (
    MINIO_BASE_URL,
    STATUS_DRAFT,
    STATUS_PUBLISHED,
    construction_resources,
)

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def published_resources():
    return [r for r in construction_resources if r["resource_status"] == STATUS_PUBLISHED]


DESCRIPTION_HEAD_LENGTH = 70


def with_likes_count(resource):
    card = dict(resource)
    card["likes_count"] = len(resource["liked_by"])

    description = resource["resource_description"]
    if len(description) > DESCRIPTION_HEAD_LENGTH:
        cut = description.rfind(" ", 0, DESCRIPTION_HEAD_LENGTH)
        if cut == -1:
            cut = DESCRIPTION_HEAD_LENGTH
        card["description_head"] = description[:cut]
        card["description_tail"] = description[cut:]
    else:
        card["description_head"] = description
        card["description_tail"] = ""

    return card


@router.get("/construction-resources")
def get_construction_resource_catalog(request: Request, maxHistoricalPrice: str = ""):
    resources = published_resources()
    prices = [r["historical_price"] for r in resources]
    price_min = min(prices, default=0)
    price_max = max(prices, default=0)

    price_limit = price_max
    price_filter = maxHistoricalPrice.strip()
    if price_filter.isdigit():
        price_limit = int(price_filter)

    resources = [r for r in resources if r["historical_price"] <= price_limit]
    cards = [with_likes_count(r) for r in resources]

    return templates.TemplateResponse(
        request=request,
        name="catalog.html",
        context={
            "construction_resources": cards,
            "price_limit": price_limit,
            "price_min": price_min,
            "price_max": price_max,
            "active_tab": "catalog",
            "minio_base_url": MINIO_BASE_URL,
        },
    )


@router.get("/construction-resources/draft")
def get_construction_resource_draft(request: Request):
    for resource in construction_resources:
        if resource["resource_status"] == STATUS_DRAFT:
            return templates.TemplateResponse(
                request=request,
                name="draft.html",
                context={
                    "construction_resource": with_likes_count(resource),
                    "active_tab": "draft",
                    "minio_base_url": MINIO_BASE_URL,
                },
            )
    raise HTTPException(status_code=404, detail="Черновик не найден")


@router.get("/construction-resources/feed")
@router.get("/construction-resources/feed/{resource_id}")
def get_construction_resource_feed(request: Request, resource_id: int = 0, next: bool = False):
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
            "construction_resource": with_likes_count(current),
            "following_id": following["id"],
            "active_tab": "feed",
            "minio_base_url": MINIO_BASE_URL,
        },
    )
