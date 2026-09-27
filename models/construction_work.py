from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String, func, text

from db.base import Base

STATUS_DRAFT = "черновик"
STATUS_PUBLISHED = "опубликован"
STATUS_DELETED = "удален"


class ConstructionWork(Base):
    __tablename__ = "construction_works"

    id = Column(Integer, primary_key=True)
    work_name = Column(String(100), nullable=False)
    work_description = Column(String(500))
    work_status = Column(String(20), nullable=False, server_default=STATUS_DRAFT)
    image_url = Column(String(255))
    video_url = Column(String(255))
    historical_price = Column(Integer)
    base_year = Column(Integer)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    formed_at = Column(DateTime)

    __table_args__ = (
        CheckConstraint(
            "work_status IN ('черновик', 'опубликован', 'удален')",
            name="construction_works_status_check",
        ),
        Index(
            "construction_works_one_draft_per_creator",
            "creator_id",
            unique=True,
            postgresql_where=text("work_status = 'черновик'"),
        ),
    )
