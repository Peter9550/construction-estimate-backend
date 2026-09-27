from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from models.construction_work import STATUS_DRAFT, STATUS_PUBLISHED, ConstructionWork
from models.work_like import WorkLike

router = APIRouter()
templates = Jinja2Templates(directory="templates")
templates.env.globals["default_image_url"] = "/static/img/default-work.png"
templates.env.globals["default_video_url"] = "/static/video/default-work.mp4"

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


async def count_likes(db: AsyncSession, work_ids):
    stmt = (
        select(WorkLike.work_id, func.count(WorkLike.id))
        .where(WorkLike.work_id.in_(work_ids))
        .group_by(WorkLike.work_id)
    )
    result = await db.execute(stmt)
    return dict(result.all())


async def find_draft(db: AsyncSession):
    stmt = select(ConstructionWork).where(
        ConstructionWork.creator_id == CURRENT_USER_ID,
        ConstructionWork.work_status == STATUS_DRAFT,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


@router.get("/construction-works")
async def get_construction_work_catalog(
    request: Request,
    maxHistoricalPrice: str = "",
    db: AsyncSession = Depends(get_db),
):
    price_range = await db.execute(
        select(func.min(ConstructionWork.historical_price), func.max(ConstructionWork.historical_price))
        .where(ConstructionWork.work_status == STATUS_PUBLISHED)
    )
    price_min, price_max = price_range.one()
    price_min = price_min or 0
    price_max = price_max or 0

    price_limit = price_max
    price_filter = maxHistoricalPrice.strip()
    if price_filter.isdigit():
        price_limit = int(price_filter)

    stmt = (
        select(ConstructionWork)
        .where(
            ConstructionWork.work_status == STATUS_PUBLISHED,
            ConstructionWork.historical_price <= price_limit,
        )
        .order_by(ConstructionWork.id)
    )
    result = await db.execute(stmt)
    works = result.scalars().all()
    likes_count = await count_likes(db, [w.id for w in works])

    return templates.TemplateResponse(
        request=request,
        name="catalog.html",
        context={
            "construction_works": works,
            "likes_count": likes_count,
            "price_limit": price_limit,
            "price_min": price_min,
            "price_max": price_max,
            "active_tab": "catalog",
        },
    )


@router.get("/construction-works/draft")
async def get_construction_work_draft(request: Request, db: AsyncSession = Depends(get_db)):
    draft = await find_draft(db)
    return templates.TemplateResponse(
        request=request,
        name="draft.html",
        context={
            "construction_work": draft,
            "active_tab": "draft",
        },
    )


@router.get("/construction-works/feed")
@router.get("/construction-works/feed/{work_id}")
async def get_construction_work_feed(
    request: Request,
    work_id: int = 0,
    next: bool = False,
    db: AsyncSession = Depends(get_db),
):
    published = (
        select(ConstructionWork)
        .where(ConstructionWork.work_status == STATUS_PUBLISHED)
        .order_by(ConstructionWork.id)
        .limit(1)
    )

    stmt = published
    if work_id and next:
        stmt = published.where(ConstructionWork.id > work_id)
    elif work_id:
        stmt = published.where(ConstructionWork.id == work_id)

    result = await db.execute(stmt)
    current = result.scalar_one_or_none()

    if current is None and next:
        result = await db.execute(published)
        current = result.scalar_one_or_none()

    if current is None:
        return PlainTextResponse("Работа не найдена", status_code=404)

    likes_count = await count_likes(db, [current.id])
    description_less, description_more = split_description(current.work_description)

    return templates.TemplateResponse(
        request=request,
        name="feed.html",
        context={
            "construction_work": current,
            "likes_count": likes_count.get(current.id, 0),
            "description_less": description_less,
            "description_more": description_more,
            "active_tab": "feed",
        },
    )


@router.post("/construction-works/draft")
async def create_construction_work_draft(
    work_name: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    if await find_draft(db) is None:
        draft = ConstructionWork(
            work_name=work_name,
            work_status=STATUS_DRAFT,
            creator_id=CURRENT_USER_ID,
        )
        db.add(draft)
        await db.commit()
    return RedirectResponse(url="/construction-works/draft", status_code=303)


@router.post("/construction-works/draft/publish")
async def publish_construction_work_draft(
    work_description: str = Form(...),
    historical_price: int = Form(...),
    base_year: int = Form(...),
    db: AsyncSession = Depends(get_db),
):
    draft = await find_draft(db)
    if draft is None:
        return PlainTextResponse("Черновик не найден", status_code=404)

    draft.work_description = work_description
    draft.historical_price = historical_price
    draft.base_year = base_year
    draft.work_status = STATUS_PUBLISHED
    draft.formed_at = func.now()
    await db.commit()

    return RedirectResponse(url=f"/construction-works/feed/{draft.id}", status_code=303)


@router.post("/construction-works/{work_id}/delete")
async def delete_construction_work(work_id: int, db: AsyncSession = Depends(get_db)):
    await db.execute(
        text("UPDATE construction_works SET work_status = 'удален' WHERE id = :id"),
        {"id": work_id},
    )
    await db.commit()
    return RedirectResponse(url="/construction-works", status_code=303)
