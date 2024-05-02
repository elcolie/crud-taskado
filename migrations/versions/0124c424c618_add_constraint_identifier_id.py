"""Add constraint (identifier, id)

Revision ID: 0124c424c618
Revises: c0e693619289
Create Date: 2024-04-29 12:33:46.755408

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0124c424c618'
down_revision: str | None = 'c0e693619289'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'currenttaskcontent', ['identifier', 'id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'currenttaskcontent', type_='unique')
    # ### end Alembic commands ###
