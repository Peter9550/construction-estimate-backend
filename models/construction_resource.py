from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String, func, text

from db.base import Base

STATUS_DRAFT = "черновик"
STATUS_PUBLISHED = "опубликован"
STATUS_DELETED = "удален"


class ConstructionResource(Base):
    __tablename__ = "construction_resources"

    id = Column(Integer, primary_key=True)
    resource_name = Column(String(100), nullable=False)
    resource_description = Column(String(500))
    resource_status = Column(String(20), nullable=False, server_default=STATUS_DRAFT)
    image_url = Column(String(255))
    video_url = Column(String(255))
    historical_price = Column(Integer)
    base_year = Column(Integer)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    formed_at = Column(DateTime)

    __table_args__ = (
        CheckConstraint(
            "resource_status IN ('черновик', 'опубликован', 'удален')",
            name="construction_resources_status_check",
        ),
        Index(
            "construction_resources_one_draft_per_creator",
            "creator_id",
            unique=True,
            postgresql_where=text("resource_status = 'черновик'"),
        ),
    )
