"""campos por arena

Uma arena pode ter vários campos, cada um com a sua agenda. Arenas existentes
ganham um "Campo 1" e todas as partidas antigas passam a apontar para ele.

Revision ID: a7c3e91d2b40
Revises: f1f05b4ebe73
Create Date: 2026-11-03 22:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a7c3e91d2b40'
down_revision: Union[str, None] = 'f1f05b4ebe73'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('campos',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('arena_id', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(length=60), nullable=False),
    sa.Column('valor_hora', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('criado_em', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('valor_hora IS NULL OR valor_hora >= 0', name='ck_campo_valor_hora'),
    sa.ForeignKeyConstraint(['arena_id'], ['arenas.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('arena_id', 'nome', name='uq_campo_arena_nome')
    )
    op.create_index(op.f('ix_campos_arena_id'), 'campos', ['arena_id'], unique=False)

    # Cada arena existente ganha um campo; partidas antigas vão para ele.
    op.execute("INSERT INTO campos (arena_id, nome) SELECT id, 'Campo 1' FROM arenas")
    with op.batch_alter_table('partidas') as batch:
        batch.add_column(sa.Column('campo_id', sa.Integer(), nullable=True))
    op.execute("UPDATE partidas SET campo_id = (SELECT c.id FROM campos c WHERE c.arena_id = partidas.arena_id)")
    with op.batch_alter_table('partidas') as batch:
        batch.alter_column('campo_id', existing_type=sa.Integer(), nullable=False)
        batch.create_foreign_key('fk_partidas_campo_id_campos', 'campos', ['campo_id'], ['id'])
        batch.create_index(batch.f('ix_partidas_campo_id'), ['campo_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('partidas') as batch:
        batch.drop_index(batch.f('ix_partidas_campo_id'))
        batch.drop_constraint('fk_partidas_campo_id_campos', type_='foreignkey')
        batch.drop_column('campo_id')
    op.drop_index(op.f('ix_campos_arena_id'), table_name='campos')
    op.drop_table('campos')
