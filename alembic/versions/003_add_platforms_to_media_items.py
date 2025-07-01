"""add platforms field to media_items

Revision ID: 003_add_platforms_to_media_items
Revises: 002_add_knowledge_base_tables
Create Date: 2025-06-30
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '003_add_platforms_to_media_items'
down_revision = '002_add_knowledge_base_tables'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('media_items', sa.Column('platforms', sa.JSON(), nullable=True))


def downgrade():
    op.drop_column('media_items', 'platforms') 