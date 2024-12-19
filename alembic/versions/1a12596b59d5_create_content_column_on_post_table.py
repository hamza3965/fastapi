"""create content column on post table

Revision ID: 1a12596b59d5
Revises: 9c40b3429973
Create Date: 2024-12-18 13:37:13.510816

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a12596b59d5'
down_revision: Union[str, None] = '9c40b3429973'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('posts', sa.Column('content', sa.String(), nullable=False))
    pass


def downgrade() -> None:
    op.drop_column('posts', 'content')
    pass
