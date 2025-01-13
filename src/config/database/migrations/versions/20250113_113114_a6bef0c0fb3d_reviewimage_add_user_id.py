"""ReviewImage_add_user_id

Revision ID: a6bef0c0fb3d
Revises: 9534d79e1a01
Create Date: 2025-01-13 11:31:14.106299

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a6bef0c0fb3d"
down_revision: Union[str, None] = "9534d79e1a01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 컬럼 추가
    op.add_column("review_images", sa.Column("user_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False))

    # 외래 키 제약 조건 생성
    op.create_foreign_key(
        "fk_review_images_user_id",  # 제약 조건 이름
        source_table="review_images",
        referent_table="users",
        local_cols=["user_id"],
        remote_cols=["id"],
    )


def downgrade() -> None:
    # 외래 키 제약 조건 삭제
    op.drop_constraint("fk_review_images_user_id", table_name="review_images", type_="foreignkey")  # 제약 조건 이름

    # 컬럼 삭제
    op.drop_column("review_images", "user_id")
