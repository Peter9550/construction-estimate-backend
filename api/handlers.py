from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from models.construction_resource import STATUS_DRAFT, STATUS_PUBLISHED, ConstructionResource
from models.resource_like import ResourceLike

router = APIRouter()
templates = Jinja2Templates(directory="templates")
templates.env.globals["default_image_url"] = "/static/img/default-resource.png"
templates.env.globals["default_video_url"] = "/static/video/default-resource.mp4"

CURRENT_USER_ID = 1
DESCRIPTION_HEAD_LENGTH = 70


def split_description(description):
    description = description or ""
    if len(description) <= DESCRIPTION_HEAD_LENGTH:
        return description, ""
    cut = description.rfind(" ", 0, DESCRIPTION_HEAD_LENGTH)
    if cut == -1:
        cut = DESCRIPTION_HEAD_LENGTH
    return description[:cut], description[cut:]


async def count_likes(db: AsyncSession, resource_ids):
    stmt = (
        select(ResourceLike.resource_id, func.count(ResourceLike.id))
        .where(ResourceLike.resource_id.in_(resource_ids))
        .group_by(ResourceLike.resource_id)
    )
    result = await db.execute(stmt)
    return dict(result.all())


async def find_draft(db: AsyncSession):
    stmt = select(ConstructionResource).where(
        ConstructionResource.creator_id == CURRENT_USER_ID,
        ConstructionResource.resource_status == STATUS_DRAFT,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


@router.get("/construction-resources")
async def get_construction_resource_catalog(
    request: Request,
    maxHistoricalPrice: str = "",
    db: AsyncSession = Depends(get_db),
):
    price_range = await db.execute(
        select(func.min(ConstructionResource.historical_price), func.max(ConstructionResource.historical_price))
        .where(ConstructionResource.resource_status == STATUS_PUBLISHED)
    )
    price_min, price_max = price_range.one()
    price_min = price_min or 0
    price_max = price_max or 0

    price_limit = price_max
    price_filter = maxHistoricalPrice.strip()
    if price_filter.isdigit():
        price_limit = int(price_filter)

    stmt = (
        select(ConstructionResource)
        .where(
            ConstructionResource.resource_status == STATUS_PUBLISHED,
            ConstructionResource.historical_price <= price_limit,
        )
        .order_by(ConstructionResource.id)
    )
    result = await db.execute(stmt)
    resources = result.scalars().all()
    likes_count = await count_likes(db, [r.id for r in resources])

    return templates.TemplateResponse(
        request=request,
        name="catalog.html",
        context={
            "construction_resources": resources,
            "likes_count": likes_count,
            "price_limit": price_limit,
            "price_min": price_min,
            "price_max": price_max,
            "active_tab": "catalog",
        },
    )


@router.get("/construction-resources/draft")
async def get_construction_resource_draft(request: Request, db: AsyncSession = Depends(get_db)):
    draft = await find_draft(db)
    return templates.TemplateResponse(
        request=request,
        name="draft.html",
        context={
            "construction_resource": draft,
            "active_tab": "draft",
        },
    )


@router.get("/construction-resources/feed")
@router.get("/construction-resources/feed/{resource_id}")
async def get_construction_resource_feed(
    request: Request,
    resource_id: int = 0,
    next: bool = False,
    db: AsyncSession = Depends(get_db),
):
    published = (
        select(ConstructionResource)
        .where(ConstructionResource.resource_status == STATUS_PUBLISHED)
        .order_by(ConstructionResource.id)
        .limit(1)
    )

    stmt = published
    if resource_id and next:
        stmt = published.where(ConstructionResource.id > resource_id)
    elif resource_id:
        stmt = published.where(ConstructionResource.id == resource_id)

    result = await db.execute(stmt)
    current = result.scalar_one_or_none()

    if current is None and next:
        result = await db.execute(published)
        current = result.scalar_one_or_none()

    if current is None:
        return PlainTextResponse("Ресурс не найден", status_code=404)

    likes_count = await count_likes(db, [current.id])
    description_head, description_tail = split_description(current.resource_description)

    return templates.TemplateResponse(
        request=request,
        name="feed.html",
        context={
            "construction_resource": current,
            "likes_count": likes_count.get(current.id, 0),
            "description_head": description_head,
            "description_tail": description_tail,
            "active_tab": "feed",
        },
    )


@router.post("/construction-resources/draft")
async def create_construction_resource_draft(
    resource_name: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    if await find_draft(db) is None:
        draft = ConstructionResource(
            resource_name=resource_name,
            resource_status=STATUS_DRAFT,
            creator_id=CURRENT_USER_ID,
        )
        db.add(draft)
        await db.commit()
    return RedirectResponse(url="/construction-resources/draft", status_code=303)


@router.post("/construction-resources/draft/publish")
async def publish_construction_resource_draft(
    resource_name: str = Form(...),
    resource_description: str = Form(...),
    historical_price: int = Form(...),
    base_year: int = Form(...),
    db: AsyncSession = Depends(get_db),
):
    draft = await find_draft(db)
    if draft is None:
        return PlainTextResponse("Черновик не найден", status_code=404)

    draft.resource_name = resource_name
    draft.resource_description = resource_description
    draft.historical_price = historical_price
    draft.base_year = base_year
    draft.resource_status = STATUS_PUBLISHED
    draft.formed_at = func.now()
    await db.commit()

    return RedirectResponse(url=f"/construction-resources/feed/{draft.id}", status_code=303)


@router.post("/construction-resources/{resource_id}/delete")
async def delete_construction_resource(resource_id: int, db: AsyncSession = Depends(get_db)):
    await db.execute(
        text("UPDATE construction_resources SET resource_status = 'удален' WHERE id = :id"),
        {"id": resource_id},
    )
    await db.commit()
    return RedirectResponse(url="/construction-resources", status_code=303)
