"""update review content field

Revision ID: 0c59f736af26
Revises: 8d3523112c16
Create Date: 2025-01-09 14:16:39.013632

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0c59f736af26"
down_revision: Union[str, None] = "8d3523112c16"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("review_images", "filepath", existing_type=sa.VARCHAR(length=255), type_=sa.Text(), nullable=True)
    op.alter_column("reviews", "content", existing_type=sa.VARCHAR(), type_=sa.Text(), existing_nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("reviews", "content", existing_type=sa.Text(), type_=sa.VARCHAR(), existing_nullable=False)
    op.alter_column("review_images", "filepath", existing_type=sa.Text(), type_=sa.VARCHAR(length=255), nullable=False)
    # ### end Alembic commands ###