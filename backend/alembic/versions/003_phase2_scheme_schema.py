"""Phase 2 scheme schema updates: geographic scope, scheme type, description, and metadata

Revision ID: 003_phase2_scheme_schema
Revises: 002_add_fine_print
Create Date: 2026-09-17 20:38:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003_phase2_scheme_schema'
down_revision: Union[str, None] = '002_add_fine_print'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Administrative and geographic fields
    op.add_column(
        'schemes',
        sa.Column('slug', sa.String(length=200), nullable=True)
    )
    op.create_index(op.f('ix_schemes_slug'), 'schemes', ['slug'], unique=False)

    op.add_column(
        'schemes',
        sa.Column('government_level', sa.String(length=50), nullable=False, server_default='Central')
    )
    op.create_index(op.f('ix_schemes_government_level'), 'schemes', ['government_level'], unique=False)

    op.add_column(
        'schemes',
        sa.Column('government_name', sa.String(length=100), nullable=False, server_default='Central Government')
    )
    op.create_index(op.f('ix_schemes_government_name'), 'schemes', ['government_name'], unique=False)

    op.add_column(
        'schemes',
        sa.Column('scheme_type', sa.String(length=100), nullable=False, server_default='welfare_scheme')
    )
    op.create_index(op.f('ix_schemes_scheme_type'), 'schemes', ['scheme_type'], unique=False)

    # Categories list for multi-category schemes
    op.add_column(
        'schemes',
        sa.Column('categories', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default=sa.text("'[]'::jsonb"))
    )

    # Detailed text and administrative entities
    op.add_column(
        'schemes',
        sa.Column('description', sa.Text(), nullable=True)
    )
    op.add_column(
        'schemes',
        sa.Column('ministry', sa.String(length=500), nullable=True)
    )
    op.add_column(
        'schemes',
        sa.Column('department', sa.String(length=500), nullable=True)
    )
    op.add_column(
        'schemes',
        sa.Column('implementing_agency', sa.String(length=500), nullable=True)
    )
    op.add_column(
        'schemes',
        sa.Column('application_url', sa.String(length=1000), nullable=True)
    )
    op.add_column(
        'schemes',
        sa.Column('contact_information', sa.Text(), nullable=True)
    )
    op.add_column(
        'schemes',
        sa.Column('source_last_checked', sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('schemes', 'source_last_checked')
    op.drop_column('schemes', 'contact_information')
    op.drop_column('schemes', 'application_url')
    op.drop_column('schemes', 'implementing_agency')
    op.drop_column('schemes', 'department')
    op.drop_column('schemes', 'ministry')
    op.drop_column('schemes', 'description')
    op.drop_column('schemes', 'categories')
    op.drop_index(op.f('ix_schemes_scheme_type'), table_name='schemes')
    op.drop_column('schemes', 'scheme_type')
    op.drop_index(op.f('ix_schemes_government_name'), table_name='schemes')
    op.drop_column('schemes', 'government_name')
    op.drop_index(op.f('ix_schemes_government_level'), table_name='schemes')
    op.drop_column('schemes', 'government_level')
    op.drop_index(op.f('ix_schemes_slug'), table_name='schemes')
    op.drop_column('schemes', 'slug')
