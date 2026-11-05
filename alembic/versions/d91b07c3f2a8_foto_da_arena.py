"""foto da arena

Revision ID: d91b07c3f2a8
Revises: c2d84f6a1e57
Create Date: 2026-11-03 23:15:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd91b07c3f2a8'
down_revision: Union[str, None] = 'c2d84f6a1e57'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('arenas') as batch:
        batch.add_column(sa.Column('foto', sa.String(length=80), nullable=True))
        batch.add_column(sa.Column('foto_foco', sa.Integer(), server_default='50', nullable=False))


def downgrade() -> None:
    with op.batch_alter_table('arenas') as batch:
        batch.drop_column('foto_foco')
        batch.drop_column('foto')
