"""steps_10_14_analytics_search_indexes

Revision ID: 20260517_steps1014
Revises: 20260517_steps49
Create Date: 2026-05-17 03:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260517_steps1014"
down_revision = "20260517_steps49"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── SavedFilter table ─────────────────────────────────────────────────────
    op.create_table(
        "saved_filters",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("filter_params", sa.JSON(), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_saved_filters_user_id"), "saved_filters", ["user_id"], unique=False)

    # ── Additional indexes for analytics performance ──────────────────────────
    # Contracts
    op.create_index(
        "ix_contracts_created_at",
        "contracts",
        ["created_at"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "ix_contracts_updated_at",
        "contracts",
        ["updated_at"],
        unique=False,
        if_not_exists=True,
    )

    # Emails date index (already exists via model, but ensure)
    # EmailClassification composite index
    op.create_index(
        "ix_email_classifications_category_urgency",
        "email_classifications",
        ["category", "urgency"],
        unique=False,
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("ix_email_classifications_category_urgency", table_name="email_classifications")
    op.drop_index("ix_contracts_updated_at", table_name="contracts")
    op.drop_index("ix_contracts_created_at", table_name="contracts")
    op.drop_index(op.f("ix_saved_filters_user_id"), table_name="saved_filters")
    op.drop_table("saved_filters")
