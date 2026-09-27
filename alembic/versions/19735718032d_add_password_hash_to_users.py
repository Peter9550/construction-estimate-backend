"""add password hash to users

Revision ID: 19735718032d
Revises: dda7a6a9a2b2
Create Date: 2026-09-27 22:31:50.385777

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '19735718032d'
down_revision: Union[str, Sequence[str], None] = 'dda7a6a9a2b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('users', sa.Column('password_hash', sa.String(length=64), nullable=True))

def downgrade() -> None:
    op.drop_column('users', 'password_hash')
