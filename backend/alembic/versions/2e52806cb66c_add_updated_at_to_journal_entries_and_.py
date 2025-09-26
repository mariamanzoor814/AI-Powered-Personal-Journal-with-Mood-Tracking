"""add updated_at to journal_entries and extend mood_analysis

Revision ID: 2e52806cb66c
Revises: 62abeb6cb0ec
Create Date: 2025-09-25 11:17:05.632172

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2e52806cb66c'
down_revision: Union[str, Sequence[str], None] = '62abeb6cb0ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("journal_entries", sa.Column("updated_at", sa.TIMESTAMP(), nullable=True))

    op.add_column("mood_analysis", sa.Column("sentiment", sa.String(), nullable=True))
    op.add_column("mood_analysis", sa.Column("emotion", sa.String(), nullable=True))
    op.add_column("mood_analysis", sa.Column("score", sa.Float(), nullable=True))
    op.add_column("mood_analysis", sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("now()"), nullable=True))

    op.create_foreign_key("fk_entry", "mood_analysis", "journal_entries", ["entry_id"], ["id"])

def downgrade() -> None:
    op.drop_constraint("fk_entry", "mood_analysis", type_="foreignkey")
    op.drop_column("mood_analysis", "created_at")
    op.drop_column("mood_analysis", "score")
    op.drop_column("mood_analysis", "emotion")
    op.drop_column("mood_analysis", "sentiment")
    op.drop_column("journal_entries", "updated_at")