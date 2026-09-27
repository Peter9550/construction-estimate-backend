from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint

from db.base import Base


class WorkLike(Base):
    __tablename__ = "work_likes"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    work_id = Column(Integer, ForeignKey("construction_works.id", ondelete="RESTRICT"), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "work_id", name="work_likes_user_work_unique"),
    )
