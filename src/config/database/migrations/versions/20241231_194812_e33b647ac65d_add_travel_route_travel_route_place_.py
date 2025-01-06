"""Add travel_route, travel_route_place table

Revision ID: e33b647ac65d
Revises: 29690dffa788
Create Date: 2024-12-31 19:48:12.575721

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e33b647ac65d"
down_revision: Union[str, None] = "29690dffa788"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "travelroute",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("regions", sa.JSON(), nullable=False),
        sa.Column("themes", sa.JSON(), nullable=False),
        sa.Column("breakfast", sa.Boolean(), nullable=False),
        sa.Column("morning", sa.Integer(), nullable=False),
        sa.Column("lunch", sa.Boolean(), nullable=False),
        sa.Column("afternoon", sa.Integer(), nullable=False),
        sa.Column("dinner", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "travelrouteplace",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("travel_route_id", sa.Integer(), nullable=True),
        sa.Column("place_id", sa.Integer(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("route_time", sa.DateTime(), nullable=False),
        sa.Column("distance", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["place_id"],
            ["place.id"],
        ),
        sa.ForeignKeyConstraint(
            ["travel_route_id"],
            ["travelroute.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.alter_column("place", "created_at", existing_type=postgresql.TIMESTAMP(timezone=True), nullable=False)
    op.alter_column("place", "updated_at", existing_type=postgresql.TIMESTAMP(timezone=True), nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("place", "updated_at", existing_type=postgresql.TIMESTAMP(timezone=True), nullable=True)
    op.alter_column("place", "created_at", existing_type=postgresql.TIMESTAMP(timezone=True), nullable=True)
    op.drop_table("travelrouteplace")
    op.drop_table("travelroute")
    # ### end Alembic commands ###