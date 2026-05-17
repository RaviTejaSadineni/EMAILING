"""step2_import_engine_columns

Revision ID: 20260517_step2
Revises: 
Create Date: 2026-05-17 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260517_step2"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("emails", sa.Column("in_reply_to", sa.String(length=500), nullable=True))
    op.add_column("emails", sa.Column("references", sa.JSON(), nullable=True))
    op.create_index(op.f("ix_emails_in_reply_to"), "emails", ["in_reply_to"], unique=False)

    op.add_column("import_jobs", sa.Column("resume_offset", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("import_jobs", sa.Column("upload_path", sa.String(length=1024), nullable=True))

    import_status_enum = sa.Enum("pending", "processing", "completed", "failed", "cancelled", name="importstatus")
    import_status_enum.create(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    op.drop_column("import_jobs", "upload_path")
    op.drop_column("import_jobs", "resume_offset")

    op.drop_index(op.f("ix_emails_in_reply_to"), table_name="emails")
    op.drop_column("emails", "references")
    op.drop_column("emails", "in_reply_to")
