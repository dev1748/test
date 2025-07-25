"""Added ai_pred to database task model for ai predictions

Revision ID: 64586a874952
Revises: 35e5321bc5e5
Create Date: 2025-07-12 12:22:42.268480

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '64586a874952'
down_revision: Union[str, Sequence[str], None] = '35e5321bc5e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tasks', sa.Column('ai_pred', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('tasks', 'ai_pred')
    # ### end Alembic commands ###
