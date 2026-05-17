"""steps_4_9_ai_pipeline_columns

Revision ID: 20260517_steps49
Revises: 20260517_step2
Create Date: 2026-05-17 02:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260517_steps49"
down_revision = "20260517_step2"
branch_labels = None
depends_on = None


processing_job_type = sa.Enum(
    "classification",
    "thread_merge",
    "contract_extraction",
    "stakeholder_extraction",
    "lifecycle_detection",
    name="processingjobtype",
)
processing_job_status = sa.Enum("pending", "in_progress", "completed", "failed", name="processingjobstatus")


def upgrade() -> None:
    processing_job_type.create(op.get_bind(), checkfirst=True)
    processing_job_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "processing_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("job_type", processing_job_type, nullable=False),
        sa.Column("status", processing_job_status, nullable=False),
        sa.Column("progress", sa.Float(), nullable=False, server_default="0"),
        sa.Column("total_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_processing_jobs_user_id"), "processing_jobs", ["user_id"], unique=False)
    op.create_index(op.f("ix_processing_jobs_job_type"), "processing_jobs", ["job_type"], unique=False)
    op.create_index(op.f("ix_processing_jobs_status"), "processing_jobs", ["status"], unique=False)

    op.add_column("contracts", sa.Column("key_clauses", sa.JSON(), nullable=True))
    op.add_column("contracts", sa.Column("contract_value", sa.Float(), nullable=True))
    op.add_column("contracts", sa.Column("effective_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("contracts", sa.Column("expiry_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("contracts", sa.Column("delay_reasons", sa.JSON(), nullable=True))
    op.add_column("contracts", sa.Column("ai_summary", sa.Text(), nullable=True))

    op.add_column("stakeholders", sa.Column("response_time_distribution", sa.JSON(), nullable=True))
    op.add_column("stakeholders", sa.Column("communication_patterns", sa.JSON(), nullable=True))
    op.add_column("stakeholders", sa.Column("influence_score", sa.Float(), nullable=True))
    op.add_column("stakeholders", sa.Column("department_mentions", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("stakeholders", "department_mentions")
    op.drop_column("stakeholders", "influence_score")
    op.drop_column("stakeholders", "communication_patterns")
    op.drop_column("stakeholders", "response_time_distribution")

    op.drop_column("contracts", "ai_summary")
    op.drop_column("contracts", "delay_reasons")
    op.drop_column("contracts", "expiry_date")
    op.drop_column("contracts", "effective_date")
    op.drop_column("contracts", "contract_value")
    op.drop_column("contracts", "key_clauses")

    op.drop_index(op.f("ix_processing_jobs_status"), table_name="processing_jobs")
    op.drop_index(op.f("ix_processing_jobs_job_type"), table_name="processing_jobs")
    op.drop_index(op.f("ix_processing_jobs_user_id"), table_name="processing_jobs")
    op.drop_table("processing_jobs")

    processing_job_status.drop(op.get_bind(), checkfirst=True)
    processing_job_type.drop(op.get_bind(), checkfirst=True)
