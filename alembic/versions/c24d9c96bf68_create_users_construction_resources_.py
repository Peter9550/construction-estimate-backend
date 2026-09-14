"""create users construction_resources resource_likes

Revision ID: c24d9c96bf68
Revises: 
Create Date: 2026-09-13 15:49:46.992096

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'c24d9c96bf68'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_login', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_login')
    )
    op.create_table('construction_resources',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('resource_name', sa.String(length=100), nullable=False),
    sa.Column('resource_description', sa.String(length=500), nullable=True),
    sa.Column('resource_status', sa.String(length=20), server_default='черновик', nullable=False),
    sa.Column('image_url', sa.String(length=255), nullable=True),
    sa.Column('video_url', sa.String(length=255), nullable=True),
    sa.Column('historical_price', sa.Integer(), nullable=True),
    sa.Column('base_year', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('creator_id', sa.Integer(), nullable=False),
    sa.Column('formed_at', sa.DateTime(), nullable=True),
    sa.CheckConstraint("resource_status IN ('черновик', 'опубликован', 'удален')", name='construction_resources_status_check'),
    sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('construction_resources_one_draft_per_creator', 'construction_resources', ['creator_id'], unique=True, postgresql_where=sa.text("resource_status = 'черновик'"))
    op.create_table('resource_likes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('resource_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['resource_id'], ['construction_resources.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'resource_id', name='resource_likes_user_resource_unique')
    )

def downgrade() -> None:
    op.drop_table('resource_likes')
    op.drop_index('construction_resources_one_draft_per_creator', table_name='construction_resources', postgresql_where=sa.text("resource_status = 'черновик'"))
    op.drop_table('construction_resources')
    op.drop_table('users')
