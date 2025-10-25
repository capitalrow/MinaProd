"""CROWN+ Event Infrastructure: Add trace_id and event_ledger

Revision ID: crown_plus_events_001
Revises: 1d4f13bc9042
Create Date: 2025-10-25 15:04:41

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'crown_plus_events_001'
down_revision = '1d4f13bc9042'
branch_labels = None
depends_on = None


def upgrade():
    # Add trace_id to sessions table
    op.add_column('sessions', sa.Column('trace_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Backfill trace_id for existing sessions with unique UUIDs
    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE sessions 
        SET trace_id = gen_random_uuid() 
        WHERE trace_id IS NULL
    """))
    
    # Make trace_id NOT NULL after backfill
    op.alter_column('sessions', 'trace_id', nullable=False)
    
    # Create unique index on trace_id
    op.create_index('ix_sessions_trace_id', 'sessions', ['trace_id'], unique=True)
    
    # Create event_ledger table
    op.create_table(
        'event_ledger',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('trace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('event_sequence', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('session_id', sa.Integer(), nullable=True),
        sa.Column('event_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('event_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='success'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for event_ledger
    op.create_index('ix_event_ledger_trace_id', 'event_ledger', ['trace_id'])
    op.create_index('ix_event_ledger_event_type', 'event_ledger', ['event_type'])
    op.create_index('ix_event_ledger_session_id', 'event_ledger', ['session_id'])
    op.create_index('ix_event_ledger_trace_sequence', 'event_ledger', ['trace_id', 'event_sequence'])
    op.create_index('ix_event_ledger_session_type', 'event_ledger', ['session_id', 'event_type'])
    op.create_index('ix_event_ledger_type_created', 'event_ledger', ['event_type', 'created_at'])


def downgrade():
    # Drop event_ledger table and its indexes
    op.drop_index('ix_event_ledger_type_created', table_name='event_ledger')
    op.drop_index('ix_event_ledger_session_type', table_name='event_ledger')
    op.drop_index('ix_event_ledger_trace_sequence', table_name='event_ledger')
    op.drop_index('ix_event_ledger_session_id', table_name='event_ledger')
    op.drop_index('ix_event_ledger_event_type', table_name='event_ledger')
    op.drop_index('ix_event_ledger_trace_id', table_name='event_ledger')
    op.drop_table('event_ledger')
    
    # Drop trace_id from sessions
    op.drop_index('ix_sessions_trace_id', table_name='sessions')
    op.drop_column('sessions', 'trace_id')
