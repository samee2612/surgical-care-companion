"""Add conversation and conversation_message tables

Revision ID: abc123def456
Revises: f9f80bf16448
Create Date: 2025-01-17 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'abc123def456'
down_revision = 'f9f80bf16448'
branch_labels = None
depends_on = None

def upgrade():
    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('patient_id', sa.String(), nullable=False),
        sa.Column('call_sid', sa.String(), nullable=True),
        sa.Column('phone_number', sa.String(), nullable=False),
        sa.Column('call_direction', sa.String(), nullable=True),
        sa.Column('call_status', sa.String(), nullable=True),
        sa.Column('call_duration', sa.Integer(), nullable=True),
        sa.Column('conversation_json', sa.JSON(), nullable=True),
        sa.Column('transcript', sa.Text(), nullable=True),
        sa.Column('intent', sa.String(), nullable=True),
        sa.Column('entities', sa.JSON(), nullable=True),
        sa.Column('sentiment', sa.String(), nullable=True),
        sa.Column('urgency_level', sa.String(), nullable=True),
        sa.Column('symptoms', sa.JSON(), nullable=True),
        sa.Column('pain_level', sa.Integer(), nullable=True),
        sa.Column('concerns', sa.JSON(), nullable=True),
        sa.Column('actions_required', sa.JSON(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_conversations_id', 'conversations', ['id'])
    op.create_index('ix_conversations_call_sid', 'conversations', ['call_sid'])
    
    # Create conversation_messages table
    op.create_table(
        'conversation_messages',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('conversation_id', sa.String(), nullable=False),
        sa.Column('message_type', sa.String(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('audio_url', sa.String(), nullable=True),
        sa.Column('transcript_confidence', sa.Integer(), nullable=True),
        sa.Column('processing_time', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_conversation_messages_id', 'conversation_messages', ['id'])

def downgrade():
    # Drop conversation_messages table
    op.drop_index('ix_conversation_messages_id', table_name='conversation_messages')
    op.drop_table('conversation_messages')
    
    # Drop conversations table
    op.drop_index('ix_conversations_call_sid', table_name='conversations')
    op.drop_index('ix_conversations_id', table_name='conversations')
    op.drop_table('conversations')
