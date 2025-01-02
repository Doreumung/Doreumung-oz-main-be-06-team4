"""merge heads

Revision ID: d9619168fb67
Revises: eb7c15a34784, 29690dffa788
Create Date: 2024-12-31 16:03:27.342956

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9619168fb67'
down_revision: Union[str, None] = ('eb7c15a34784', '29690dffa788')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
