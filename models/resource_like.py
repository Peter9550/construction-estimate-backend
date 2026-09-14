from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint

from db.base import Base


class ResourceLike(Base):
    __tablename__ = "resource_likes"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    resource_id = Column(Integer, ForeignKey("construction_resources.id", ondelete="RESTRICT"), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "resource_id", name="resource_likes_user_resource_unique"),
    )
