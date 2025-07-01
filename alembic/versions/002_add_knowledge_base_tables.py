"""Add knowledge base and responder tables

Revision ID: 002
Revises: 001
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    # Create knowledge_files table
    op.create_table(
        'knowledge_files',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('original_filename', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('file_type', sa.String(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('upload_timestamp', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create responder_configurations table
    op.create_table(
        'responder_configurations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('personality', sa.String(), nullable=False),
        sa.Column('capabilities', sa.JSON(), nullable=False),
        sa.Column('business_info', sa.JSON(), nullable=False),
        sa.Column('knowledge_base', sa.JSON(), nullable=False),
        sa.Column('escalation_keywords', sa.JSON(), nullable=False),
        sa.Column('response_style', sa.String(), nullable=False),
        sa.Column('max_response_length', sa.Integer(), nullable=False),
        sa.Column('greeting_enabled', sa.Boolean(), nullable=False),
        sa.Column('follow_up_enabled', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create responder_conversations table
    op.create_table(
        'responder_conversations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('platform_user_id', sa.String(), nullable=False),
        sa.Column('platform', sa.String(), nullable=False),
        sa.Column('conversation_data', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('satisfaction_score', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('last_activity', sa.DateTime(), nullable=True),
        sa.Column('escalated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create responder_messages table
    op.create_table(
        'responder_messages',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('conversation_id', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('intent', sa.String(), nullable=True),
        sa.Column('confidence', sa.Integer(), nullable=True),
        sa.Column('message_metadata', sa.JSON(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['responder_conversations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    # Drop tables in reverse order
    op.drop_table('responder_messages')
    op.drop_table('responder_conversations')
    op.drop_table('responder_configurations')
    op.drop_table('knowledge_files') 