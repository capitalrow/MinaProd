"""Add archive fields to meeting model (CROWN⁴ Phase 4)

Revision ID: add_meeting_archive_crown4
Revises: 1d4f13bc9042
Create Date: 2025-10-28 01:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_meeting_archive_crown4'
down_revision = '1d4f13bc9042'
branch_labels = None
depends_on = None


def upgrade():
    """Add archive fields to meetings table"""
    with op.batch_alter_table('meetings', schema=None) as batch_op:
        # Add archived boolean column with default False
        batch_op.add_column(sa.Column('archived', sa.Boolean(), nullable=False, server_default='false'))
        
        # Add archived_at timestamp column (nullable)
        batch_op.add_column(sa.Column('archived_at', sa.DateTime(), nullable=True))
        
        # Add archived_by_user_id foreign key (nullable)
        batch_op.add_column(sa.Column('archived_by_user_id', sa.Integer(), nullable=True))
        
        # Create index on archived for fast filtering
        batch_op.create_index(batch_op.f('ix_meetings_archived'), ['archived'], unique=False)
        
        # Add foreign key constraint
        batch_op.create_foreign_key('fk_meetings_archived_by_user', 'users', ['archived_by_user_id'], ['id'])


def downgrade():
    """Remove archive fields from meetings table"""
    with op.batch_alter_table('meetings', schema=None) as batch_op:
        # Drop foreign key constraint
        batch_op.drop_constraint('fk_meetings_archived_by_user', type_='foreignkey')
        
        # Drop index
        batch_op.drop_index(batch_op.f('ix_meetings_archived'))
        
        # Drop columns
        batch_op.drop_column('archived_by_user_id')
        batch_op.drop_column('archived_at')
        batch_op.drop_column('archived')
