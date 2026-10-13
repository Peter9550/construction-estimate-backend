"""make media urls and password hash required

Revision ID: 1cbe3435b8c4
Revises: 19735718032d
Create Date: 2026-10-13 19:08:31.261317

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from core.storage import DEFAULT_IMAGE_URL, DEFAULT_VIDEO_URL


revision: str = '1cbe3435b8c4'
down_revision: Union[str, Sequence[str], None] = '19735718032d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.execute(sa.text("UPDATE construction_works SET image_url = :url WHERE image_url IS NULL").bindparams(url=DEFAULT_IMAGE_URL))
    op.execute(sa.text("UPDATE construction_works SET video_url = :url WHERE video_url IS NULL").bindparams(url=DEFAULT_VIDEO_URL))
    op.execute(sa.text("UPDATE users SET password_hash = encode(sha256('password123'), 'hex') WHERE password_hash IS NULL"))
    op.alter_column("construction_works", "image_url", existing_type=sa.String(length=255), nullable=False)
    op.alter_column("construction_works", "video_url", existing_type=sa.String(length=255), nullable=False)
    op.alter_column("users", "password_hash", existing_type=sa.String(length=64), nullable=False)


def downgrade() -> None:
    op.alter_column("users", "password_hash", existing_type=sa.String(length=64), nullable=True)
    op.alter_column("construction_works", "video_url", existing_type=sa.String(length=255), nullable=True)
    op.alter_column("construction_works", "image_url", existing_type=sa.String(length=255), nullable=True)
