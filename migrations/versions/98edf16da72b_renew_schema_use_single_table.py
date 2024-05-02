"""Renew schema use single table.

Revision ID: 98edf16da72b
Revises:
Create Date: 2024-04-27 13:57:01.192961

"""
from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '98edf16da72b'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'taskcontent',
        sa.Column('identifier', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column(
            'status',
            sa.Enum('pending', 'in_progress', 'completed', name='statusenum'),
            nullable=False,
        ),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['created_by'],
            ['user.id'],
        ),
        sa.PrimaryKeyConstraint('identifier'),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('taskcontent')
    op.drop_table('user')
    # ### end Alembic commands ###
