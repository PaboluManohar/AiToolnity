"""Create the initial AIToolnity schema."""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def _create_index_if_missing(
    index_name: str,
    table_name: str,
    column_names: list[str],
    *,
    unique: bool,
) -> None:
    inspector = sa.inspect(op.get_bind())
    indexes = {index["name"] for index in inspector.get_indexes(table_name)}
    if index_name not in indexes:
        op.create_index(index_name, table_name, column_names, unique=unique)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("users"):
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("google_sub", sa.String(length=255), nullable=False),
            sa.Column("email", sa.String(length=320), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
        )
    _create_index_if_missing("ix_users_google_sub", "users", ["google_sub"], unique=True)
    _create_index_if_missing("ix_users_email", "users", ["email"], unique=True)

    if not inspector.has_table("ai_settings"):
        op.create_table(
            "ai_settings",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("encrypted_api_key", sa.Text(), nullable=True),
            sa.Column("model", sa.String(length=255), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id"),
        )

    if not inspector.has_table("executions"):
        op.create_table(
            "executions",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("parent_id", sa.Integer(), nullable=True),
            sa.Column("tool_id", sa.String(length=255), nullable=False),
            sa.Column("input_data", sa.JSON(), nullable=False),
            sa.Column("result", sa.Text(), nullable=False),
            sa.Column("model", sa.String(length=255), nullable=False),
            sa.Column("tone", sa.String(length=80), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.CheckConstraint(
                "length(result) > 0", name="ck_execution_result_not_empty"
            ),
            sa.ForeignKeyConstraint(["parent_id"], ["executions.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    _create_index_if_missing(
        "ix_executions_user_id", "executions", ["user_id"], unique=False
    )
    _create_index_if_missing(
        "ix_executions_tool_id", "executions", ["tool_id"], unique=False
    )

    if not inspector.has_table("execution_attempts"):
        op.create_table(
            "execution_attempts",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("request_key", sa.String(length=64), nullable=False),
            sa.Column("request_hash", sa.String(length=64), nullable=False),
            sa.Column(
                "status",
                sa.String(length=16),
                server_default=sa.text("'pending'"),
                nullable=False,
            ),
            sa.Column("execution_id", sa.Integer(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.CheckConstraint(
                "status IN ('pending', 'complete')", name="ck_attempt_status"
            ),
            sa.ForeignKeyConstraint(
                ["execution_id"], ["executions.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "user_id", "request_key", name="uq_attempt_user_request_key"
            ),
        )


def downgrade() -> None:
    op.drop_table("execution_attempts")
    op.drop_index("ix_executions_tool_id", table_name="executions")
    op.drop_index("ix_executions_user_id", table_name="executions")
    op.drop_table("executions")
    op.drop_table("ai_settings")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_google_sub", table_name="users")
    op.drop_table("users")
