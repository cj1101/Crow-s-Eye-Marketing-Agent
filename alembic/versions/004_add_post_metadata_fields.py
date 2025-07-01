"""add post metadata fields to media_items

Revision ID: 004_add_post_metadata_fields
Revises: 003_add_platforms_to_media_items
Create Date: 2025-06-30
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '004_add_post_metadata_fields'
down_revision = '003_add_platforms_to_media_items'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('media_items', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('media_items', sa.Column('status', sa.String(50), nullable=True, default='draft'))
    op.add_column('media_items', sa.Column('post_metadata', sa.JSON(), nullable=True))
    
    # Add index on status column for efficient filtering
    op.create_index('ix_media_items_status', 'media_items', ['status'])


def downgrade():
    op.drop_index('ix_media_items_status', 'media_items')
    op.drop_column('media_items', 'post_metadata')
    op.drop_column('media_items', 'status')
    op.drop_column('media_items', 'description') 