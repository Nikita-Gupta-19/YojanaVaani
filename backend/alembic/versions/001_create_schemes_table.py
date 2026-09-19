"""Create schemes table

Revision ID: 001_create_schemes
Revises: 
Create Date: 2026-09-11 16:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_create_schemes'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'schemes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=500), nullable=False),
        sa.Column('category', sa.String(length=200), nullable=False),
        sa.Column('ministry_or_department', sa.String(length=500), nullable=True),
        sa.Column('eligibility_criteria', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('benefits', sa.Text(), nullable=True),
        sa.Column('required_documents', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('application_process', sa.Text(), nullable=True),
        sa.Column('source_url', sa.String(length=1000), nullable=False),
        sa.Column('last_scraped_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_schemes_id'), 'schemes', ['id'], unique=False)
    op.create_index(op.f('ix_schemes_name'), 'schemes', ['name'], unique=False)
    op.create_index(op.f('ix_schemes_category'), 'schemes', ['category'], unique=False)
    op.create_index(op.f('ix_schemes_source_url'), 'schemes', ['source_url'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_schemes_source_url'), table_name='schemes')
    op.drop_index(op.f('ix_schemes_category'), table_name='schemes')
    op.drop_index(op.f('ix_schemes_name'), table_name='schemes')
    op.drop_index(op.f('ix_schemes_id'), table_name='schemes')
    op.drop_table('schemes')
