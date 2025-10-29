"""Add CROWN⁴.5 fields to tasks table

Revision ID: crown45_task_fields
Revises: 1d4f13bc9042
Create Date: 2025-10-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'crown45_task_fields'
down_revision = '1d4f13bc9042'
branch_labels = None
depends_on = None


def upgrade():
    """Add CROWN⁴.5 fields to tasks table for event sequencing and deduplication."""
    
    # Add CROWN⁴.5: Deduplication and origin tracking
    op.add_column('tasks', sa.Column('origin_hash', sa.String(64), nullable=True))
    op.add_column('tasks', sa.Column('source', sa.String(32), nullable=False, server_default='manual'))
    
    # Add CROWN⁴.5: Event sequencing and conflict resolution
    op.add_column('tasks', sa.Column('vector_clock_token', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('tasks', sa.Column('reconciliation_status', sa.String(32), nullable=False, server_default='synced'))
    
    # Add CROWN⁴.5: Transcript linking
    op.add_column('tasks', sa.Column('transcript_span', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    
    # Add CROWN⁴.5: Emotional architecture
    op.add_column('tasks', sa.Column('emotional_state', sa.String(32), nullable=True))
    
    # Add CROWN⁴.5: Task labels for organization
    op.add_column('tasks', sa.Column('labels', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    
    # Create indexes for CROWN⁴.5 fields
    op.create_index('ix_tasks_origin_hash', 'tasks', ['origin_hash'])
    op.create_index('ix_tasks_reconciliation', 'tasks', ['reconciliation_status'])
    op.create_index('ix_tasks_source', 'tasks', ['source'])
    # Note: vector_clock_token doesn't need an index as it's used for conflict resolution, not frequent querying


def downgrade():
    """Remove CROWN⁴.5 fields from tasks table."""
    
    # Drop indexes
    op.drop_index('ix_tasks_source', table_name='tasks')
    op.drop_index('ix_tasks_reconciliation', table_name='tasks')
    op.drop_index('ix_tasks_origin_hash', table_name='tasks')
    
    # Drop columns
    op.drop_column('tasks', 'labels')
    op.drop_column('tasks', 'emotional_state')
    op.drop_column('tasks', 'transcript_span')
    op.drop_column('tasks', 'reconciliation_status')
    op.drop_column('tasks', 'vector_clock_token')
    op.drop_column('tasks', 'source')
    op.drop_column('tasks', 'origin_hash')
