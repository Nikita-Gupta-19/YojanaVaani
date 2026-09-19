"""Consolidate schemes schema: Add lifecycle, beneficiary type, family linking, confidence, and drop legacy columns

Revision ID: 004_consolidate_schemes_schema
Revises: 003_phase2_scheme_schema
Create Date: 2026-09-18 12:15:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004_consolidate_schemes_schema'
down_revision: Union[str, None] = '003_phase2_scheme_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add new structured columns directly to schemes table
    op.add_column(
        'schemes',
        sa.Column('beneficiary_type', sa.String(length=50), nullable=False, server_default='individual')
    )
    op.create_index(op.f('ix_schemes_beneficiary_type'), 'schemes', ['beneficiary_type'], unique=False)

    op.add_column(
        'schemes',
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active')
    )
    op.create_index(op.f('ix_schemes_status'), 'schemes', ['status'], unique=False)

    op.add_column(
        'schemes',
        sa.Column('scheme_family', sa.String(length=100), nullable=True)
    )
    op.create_index(op.f('ix_schemes_scheme_family'), 'schemes', ['scheme_family'], unique=False)

    op.add_column(
        'schemes',
        sa.Column('parent_scheme_id', sa.Integer(), nullable=True)
    )

    op.add_column(
        'schemes',
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='1.0')
    )

    op.add_column(
        'schemes',
        sa.Column('extraction_verified', sa.Boolean(), nullable=False, server_default=sa.text('true'))
    )

    op.add_column(
        'schemes',
        sa.Column('income_tiers', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default=sa.text("'[]'::jsonb"))
    )

    op.add_column(
        'schemes',
        sa.Column('review_flags', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default=sa.text("'[]'::jsonb"))
    )

    # 2. Drop redundant legacy column ministry_or_department
    op.drop_column('schemes', 'ministry_or_department')

    # 3. Drop temporary table schemes_preprocessed if it exists (unifying into single table)
    op.execute('DROP TABLE IF EXISTS schemes_preprocessed')


def downgrade() -> None:
    op.add_column(
        'schemes',
        sa.Column('ministry_or_department', sa.String(length=500), nullable=True)
    )
    op.drop_column('schemes', 'review_flags')
    op.drop_column('schemes', 'income_tiers')
    op.drop_column('schemes', 'extraction_verified')
    op.drop_column('schemes', 'confidence_score')
    op.drop_column('schemes', 'parent_scheme_id')
    op.drop_index(op.f('ix_schemes_scheme_family'), table_name='schemes')
    op.drop_column('schemes', 'scheme_family')
    op.drop_index(op.f('ix_schemes_status'), table_name='schemes')
    op.drop_column('schemes', 'status')
    op.drop_index(op.f('ix_schemes_beneficiary_type'), table_name='schemes')
    op.drop_column('schemes', 'beneficiary_type')
