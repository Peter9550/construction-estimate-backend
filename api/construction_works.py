from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.current_user import CurrentUser, get_current_user
from core.storage import upload_file
from db.session import get_db
from models.construction_work import STATUS_DELETED, STATUS_DRAFT, STATUS_PUBLISHED, ConstructionWork
from models.work_like import WorkLike
from schemas.construction_work import ConstructionWorkOut, ConstructionWorkPublish, WorkLikeIn

router = APIRouter(prefix="/api/construction-works")


async def serialize_works(db: AsyncSession, works, user: CurrentUser):
    work_ids = [work.id for work in works]

    result = await db.execute(
        select(WorkLike.work_id, func.count(WorkLike.id))
        .where(WorkLike.work_id.in_(work_ids))
        .group_by(WorkLike.work_id)
    )
    likes_count = dict(result.all())

    result = await db.execute(
        select(WorkLike.work_id).where(WorkLike.work_id.in_(work_ids), WorkLike.user_id == user.id)
    )
    liked_ids = set(result.scalars().all())

    serialized = []
    for work in works:
        serialized.append(
            ConstructionWorkOut(
                id=work.id,
                work_name=work.work_name,
                work_description=work.work_description,
                work_status=work.work_status,
                image_url=work.image_url,
                video_url=work.video_url,
                historical_price=work.historical_price,
                base_year=work.base_year,
                created_at=work.created_at,
                formed_at=work.formed_at,
                likes_count=likes_count.get(work.id, 0),
                is_mine=int(work.creator_id == user.id),
                is_liked=int(work.id in liked_ids),
            )
        )
    return serialized


async def find_draft(db: AsyncSession, user: CurrentUser):
    result = await db.execute(
        select(ConstructionWork).where(
            ConstructionWork.creator_id == user.id,
            ConstructionWork.work_status == STATUS_DRAFT,
        )
    )
    return result.scalar_one_or_none()


@router.get("", response_model=list[ConstructionWorkOut])
async def get_construction_works(
    max_historical_price: int | None = None,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    stmt = select(ConstructionWork).where(ConstructionWork.work_status == STATUS_PUBLISHED)
    if max_historical_price is not None:
        stmt = stmt.where(ConstructionWork.historical_price <= max_historical_price)

    result = await db.execute(stmt.order_by(ConstructionWork.id))
    works = result.scalars().all()
    return await serialize_works(db, works, user)


@router.get("/feed", response_model=ConstructionWorkOut)
async def get_construction_work_feed(
    work_id: int = 0,
    next: bool = False,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
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
    work = result.scalar_one_or_none()

    if work is None and next:
        result = await db.execute(published)
        work = result.scalar_one_or_none()

    if work is None:
        raise HTTPException(status_code=404, detail="Работа не найдена")

    serialized = await serialize_works(db, [work], user)
    return serialized[0]


@router.get("/draft", response_model=ConstructionWorkOut)
async def get_construction_work_draft(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    draft = await find_draft(db, user)
    if draft is None:
        raise HTTPException(status_code=404, detail="Черновик не найден")

    serialized = await serialize_works(db, [draft], user)
    return serialized[0]


@router.post("", response_model=ConstructionWorkOut, status_code=201)
async def create_construction_work(
    work_name: str = Form(min_length=1, max_length=100),
    image: UploadFile | None = File(None),
    video: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    if await find_draft(db, user) is not None:
        raise HTTPException(status_code=400, detail="Черновик уже есть, сначала опубликуйте его")
    if image and not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Поле image должно быть изображением")
    if video and not video.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Поле video должно быть видео")

    draft = ConstructionWork(work_name=work_name, work_status=STATUS_DRAFT, creator_id=user.id)
    if image:
        draft.image_url = await upload_file(image, "image")
    if video:
        draft.video_url = await upload_file(video, "video")

    db.add(draft)
    await db.commit()
    await db.refresh(draft)

    serialized = await serialize_works(db, [draft], user)
    return serialized[0]


@router.put("/draft/publish", response_model=ConstructionWorkOut)
async def publish_construction_work(
    data: ConstructionWorkPublish,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    draft = await find_draft(db, user)
    if draft is None:
        raise HTTPException(status_code=404, detail="Черновик не найден")

    draft.work_description = data.work_description
    draft.historical_price = data.historical_price
    draft.base_year = data.base_year
    draft.work_status = STATUS_PUBLISHED
    draft.formed_at = func.now()
    await db.commit()
    await db.refresh(draft)

    serialized = await serialize_works(db, [draft], user)
    return serialized[0]


@router.delete("/{work_id}")
async def delete_construction_work(
    work_id: int,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    work = await db.get(ConstructionWork, work_id)
    if work is None or work.work_status == STATUS_DELETED:
        raise HTTPException(status_code=404, detail="Работа не найдена")
    if work.creator_id != user.id:
        raise HTTPException(status_code=403, detail="Удалять можно только свои работы")

    work.work_status = STATUS_DELETED
    await db.commit()
    return {"message": f"Работа {work_id} удалена"}


@router.post("/{work_id}/like", response_model=ConstructionWorkOut)
async def like_construction_work(
    work_id: int,
    data: WorkLikeIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    work = await db.get(ConstructionWork, work_id)
    if work is None or work.work_status != STATUS_PUBLISHED:
        raise HTTPException(status_code=404, detail="Работа не найдена")

    result = await db.execute(
        select(WorkLike).where(WorkLike.work_id == work_id, WorkLike.user_id == user.id)
    )
    like = result.scalar_one_or_none()

    if data.like == 1 and like is None:
        db.add(WorkLike(user_id=user.id, work_id=work_id))
    if data.like == 0 and like is not None:
        await db.delete(like)
    await db.commit()

    serialized = await serialize_works(db, [work], user)
    return serialized[0]
