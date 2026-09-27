"""rename construction resources to construction works

Revision ID: dda7a6a9a2b2
Revises: c24d9c96bf68
Create Date: 2026-09-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'dda7a6a9a2b2'
down_revision: Union[str, Sequence[str], None] = 'c24d9c96bf68'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UPGRADE_STATEMENTS = [
    "ALTER TABLE construction_resources RENAME TO construction_works",
    "ALTER TABLE construction_works RENAME COLUMN resource_name TO work_name",
    "ALTER TABLE construction_works RENAME COLUMN resource_description TO work_description",
    "ALTER TABLE construction_works RENAME COLUMN resource_status TO work_status",
    "ALTER TABLE construction_works RENAME CONSTRAINT construction_resources_status_check TO construction_works_status_check",
    "ALTER TABLE construction_works RENAME CONSTRAINT construction_resources_creator_id_fkey TO construction_works_creator_id_fkey",
    "ALTER INDEX construction_resources_pkey RENAME TO construction_works_pkey",
    "ALTER INDEX construction_resources_one_draft_per_creator RENAME TO construction_works_one_draft_per_creator",
    "ALTER SEQUENCE construction_resources_id_seq RENAME TO construction_works_id_seq",
    "ALTER TABLE resource_likes RENAME TO work_likes",
    "ALTER TABLE work_likes RENAME COLUMN resource_id TO work_id",
    "ALTER TABLE work_likes RENAME CONSTRAINT resource_likes_user_resource_unique TO work_likes_user_work_unique",
    "ALTER TABLE work_likes RENAME CONSTRAINT resource_likes_user_id_fkey TO work_likes_user_id_fkey",
    "ALTER TABLE work_likes RENAME CONSTRAINT resource_likes_resource_id_fkey TO work_likes_work_id_fkey",
    "ALTER INDEX resource_likes_pkey RENAME TO work_likes_pkey",
    "ALTER SEQUENCE resource_likes_id_seq RENAME TO work_likes_id_seq",
]

DOWNGRADE_STATEMENTS = [
    "ALTER SEQUENCE work_likes_id_seq RENAME TO resource_likes_id_seq",
    "ALTER INDEX work_likes_pkey RENAME TO resource_likes_pkey",
    "ALTER TABLE work_likes RENAME CONSTRAINT work_likes_work_id_fkey TO resource_likes_resource_id_fkey",
    "ALTER TABLE work_likes RENAME CONSTRAINT work_likes_user_id_fkey TO resource_likes_user_id_fkey",
    "ALTER TABLE work_likes RENAME CONSTRAINT work_likes_user_work_unique TO resource_likes_user_resource_unique",
    "ALTER TABLE work_likes RENAME COLUMN work_id TO resource_id",
    "ALTER TABLE work_likes RENAME TO resource_likes",
    "ALTER SEQUENCE construction_works_id_seq RENAME TO construction_resources_id_seq",
    "ALTER INDEX construction_works_one_draft_per_creator RENAME TO construction_resources_one_draft_per_creator",
    "ALTER INDEX construction_works_pkey RENAME TO construction_resources_pkey",
    "ALTER TABLE construction_works RENAME CONSTRAINT construction_works_creator_id_fkey TO construction_resources_creator_id_fkey",
    "ALTER TABLE construction_works RENAME CONSTRAINT construction_works_status_check TO construction_resources_status_check",
    "ALTER TABLE construction_works RENAME COLUMN work_status TO resource_status",
    "ALTER TABLE construction_works RENAME COLUMN work_description TO resource_description",
    "ALTER TABLE construction_works RENAME COLUMN work_name TO resource_name",
    "ALTER TABLE construction_works RENAME TO construction_resources",
]

def upgrade() -> None:
    for statement in UPGRADE_STATEMENTS:
        op.execute(statement)

def downgrade() -> None:
    for statement in DOWNGRADE_STATEMENTS:
        op.execute(statement)
