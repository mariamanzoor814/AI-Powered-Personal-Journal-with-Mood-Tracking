"""add recommendation to mood_analysis

Revision ID: 461fd4be7b4c
Revises: 2e52806cb66c
Create Date: 2025-09-25 11:56:08.966845

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '461fd4be7b4c'
down_revision: Union[str, Sequence[str], None] = '2e52806cb66c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "mood_analysis",
        sa.Column("recommendation", sa.Text(), nullable=True)
    )

def downgrade() -> None:
    op.drop_column("mood_analysis", "recommendation")
