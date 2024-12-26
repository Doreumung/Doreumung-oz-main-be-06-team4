"""initial

Revision ID: f0952a777a36
Revises: 
Create Date: 2024-12-26 00:44:15.109352

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f0952a777a36"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=50), nullable=False),
        sa.Column("password", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=30), nullable=False),
        sa.Column("birthday", sa.Date(), nullable=True),
        sa.Column("gender", sa.Enum("MALE", "FEMALE", name="gender"), nullable=True),
        sa.Column("phone_number", sa.String(length=20), nullable=False),
        sa.Column("oauth_id", sa.String(length=100), nullable=True),
        sa.Column("is_superuser", sa.Boolean(), nullable=True),
        sa.Column("social_provider", sa.Enum("KAKAO", "GOOGLE", name="socialprovider"), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    # ### end Alembic commands ###