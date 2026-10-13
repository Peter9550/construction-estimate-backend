from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.current_user import get_current_user, get_optional_user
from core.storage import upload_file
from db.session import get_db
from models.construction_work import STATUS_DELETED, STATUS_DRAFT, STATUS_PUBLISHED, ConstructionWork
from models.user import User
from models.work_like import WorkLike
from schemas.construction_work import ConstructionWorkOut, ConstructionWorkPublish, WorkLikeIn

router = APIRouter(prefix="/api/construction-works", tags=["Строительные работы"])


async def serialize_works(db: AsyncSession, works, user: User | None):
    work_ids = [work.id for work in works]
    user_id = user.id if user is not None else None

    result = await db.execute(
        select(WorkLike.work_id, func.count(WorkLike.id))
        .where(WorkLike.work_id.in_(work_ids))
        .group_by(WorkLike.work_id)
    )
    likes_count = dict(result.all())

    liked_ids = set()
    if user_id is not None:
        result = await db.execute(
            select(WorkLike.work_id).where(WorkLike.work_id.in_(work_ids), WorkLike.user_id == user_id)
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
                is_mine=int(work.creator_id == user_id),
                is_liked=int(work.id in liked_ids),
            )
        )
    return serialized


async def find_draft(db: AsyncSession, user: User):
    result = await db.execute(
        select(ConstructionWork).where(
            ConstructionWork.creator_id == user.id,
            ConstructionWork.work_status == STATUS_DRAFT,
        )
    )
    return result.scalar_one_or_none()


@router.get(
    "",
    response_model=list[ConstructionWorkOut],
    summary="Список работ с фильтром",
    description=(
        "Опубликованные работы, фильтр по максимальной цене в копейках. Доступен гостю. "
        "is_mine = 1, если работу создал вошедший пользователь, у гостя всегда 0."
    ),
)
async def get_construction_works(
    max_historical_price: int | None = None,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    stmt = select(ConstructionWork).where(ConstructionWork.work_status == STATUS_PUBLISHED)
    if max_historical_price is not None:
        stmt = stmt.where(ConstructionWork.historical_price <= max_historical_price)

    result = await db.execute(stmt.order_by(ConstructionWork.id))
    works = result.scalars().all()
    return await serialize_works(db, works, user)


@router.get(
    "/feed",
    response_model=ConstructionWorkOut,
    summary="Лента",
    description=(
        "Одна опубликованная работа. Без параметров - первая, с work_id - эта, с work_id и next=true - следующая. "
        "Доступна гостю. is_liked = 1, если вошедший пользователь лайкнул работу, у гостя всегда 0."
    ),
)
async def get_construction_work_feed(
    work_id: int = 0,
    next: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_optional_user),
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


@router.get(
    "/draft",
    response_model=ConstructionWorkOut,
    summary="Черновик",
    description="Черновик вошедшего пользователя, id не указывается. 401 - не выполнен вход, 404 - черновика нет.",
)
async def get_construction_work_draft(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    draft = await find_draft(db, user)
    if draft is None:
        raise HTTPException(status_code=404, detail="Черновик не найден")

    serialized = await serialize_works(db, [draft], user)
    return serialized[0]


@router.post(
    "",
    response_model=ConstructionWorkOut,
    status_code=201,
    summary="Добавление работы с фото и видео",
    description=(
        "Создаёт черновик, создатель берётся из сессии. Файлы сохраняются в MinIO, в БД ссылки. "
        "401 - не выполнен вход, 400 - черновик уже есть или файл не того типа."
    ),
)
async def create_construction_work(
    work_name: str = Form(min_length=1, max_length=100),
    image: UploadFile = File(...),
    video: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if await find_draft(db, user) is not None:
        raise HTTPException(status_code=400, detail="Черновик уже есть, сначала опубликуйте его")
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Поле image должно быть изображением")
    if not video.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Поле video должно быть видео")

    draft = ConstructionWork(
        work_name=work_name,
        work_status=STATUS_DRAFT,
        creator_id=user.id,
        image_url=await upload_file(image, "image"),
        video_url=await upload_file(video, "video"),
    )

    db.add(draft)
    await db.commit()
    await db.refresh(draft)

    serialized = await serialize_works(db, [draft], user)
    return serialized[0]


@router.put(
    "/draft/publish",
    response_model=ConstructionWorkOut,
    summary="Публикация черновика",
    description=(
        "Заполняет описание, цену и год, меняет статус на опубликован и ставит дату публикации. "
        "401 - не выполнен вход, 404 - черновика нет."
    ),
)
async def publish_construction_work(
    data: ConstructionWorkPublish,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
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


@router.delete(
    "/{work_id}",
    summary="Удаление работы",
    description="Мягкое удаление: статус удален. 401 - не выполнен вход, 403 - чужая работа, 404 - работы нет.",
)
async def delete_construction_work(
    work_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    work = await db.get(ConstructionWork, work_id)
    if work is None or work.work_status == STATUS_DELETED:
        raise HTTPException(status_code=404, detail="Работа не найдена")
    if work.creator_id != user.id:
        raise HTTPException(status_code=403, detail="Удалять можно только свои работы")

    work.work_status = STATUS_DELETED
    await db.commit()
    return {"message": f"Работа {work_id} удалена"}


@router.post(
    "/{work_id}/like",
    response_model=ConstructionWorkOut,
    summary="Лайк",
    description="like = 1 ставит лайк, like = 0 снимает. 401 - не выполнен вход, 404 - работа не опубликована.",
)
async def like_construction_work(
    work_id: int,
    data: WorkLikeIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
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
