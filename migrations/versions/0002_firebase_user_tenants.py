
"""Map Firebase users to private plagiarism-engine tenants.

Revision ID: 0002
Revises: 0001
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE firebase_user_tenants (
            firebase_uid text PRIMARY KEY,
            tenant_id uuid NOT NULL UNIQUE
                REFERENCES tenants(id) ON DELETE CASCADE,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS firebase_user_tenants")
