"""destaque da arena

Data até a qual a arena aparece com o selo "Destaque" na vitrine da página inicial.

Revision ID: c2d84f6a1e57
Revises: a7c3e91d2b40
Create Date: 2026-11-03 23:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c2d84f6a1e57'
down_revision: Union[str, None] = 'a7c3e91d2b40'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('arenas') as batch:
        batch.add_column(sa.Column('destaque_ate', sa.Date(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('arenas') as batch:
        batch.drop_column('destaque_ate')
