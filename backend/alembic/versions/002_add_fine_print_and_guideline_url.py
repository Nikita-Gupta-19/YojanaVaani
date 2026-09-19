"""Add fine_print_conditions and guideline_document_url to schemes table

Revision ID: 002_add_fine_print_and_guideline_url
Revises: 001_create_schemes
Create Date: 2026-09-16 17:45:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_add_fine_print'
down_revision: Union[str, None] = '001_create_schemes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'schemes',
        sa.Column('guideline_document_url', sa.String(length=1000), nullable=True)
    )
    op.add_column(
        'schemes',
        sa.Column(
            'fine_print_conditions',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'[]'::jsonb")
        )
    )


def downgrade() -> None:
    op.drop_column('schemes', 'fine_print_conditions')
    op.drop_column('schemes', 'guideline_document_url')
