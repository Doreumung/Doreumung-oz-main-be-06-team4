"""del username phone_num

Revision ID: 29690dffa788
Revises: 93aaf325759e
Create Date: 2024-12-31 10:58:41.537245

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "29690dffa788"
down_revision: Union[str, None] = "93aaf325759e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("users", "id", existing_type=sa.INTEGER(), type_=sa.String(length=36), existing_nullable=False)
    op.alter_column("users", "nickname", existing_type=sa.VARCHAR(length=30), nullable=False)
    op.drop_column("users", "username")
    op.drop_column("users", "phone_number")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("users", sa.Column("phone_number", sa.VARCHAR(length=20), autoincrement=False, nullable=True))
    op.add_column("users", sa.Column("username", sa.VARCHAR(length=30), autoincrement=False, nullable=False))
    op.alter_column("users", "nickname", existing_type=sa.VARCHAR(length=30), nullable=True)
    op.alter_column("users", "id", existing_type=sa.String(length=36), type_=sa.INTEGER(), existing_nullable=False)
    # ### end Alembic commands ###
