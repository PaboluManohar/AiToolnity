from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    google_sub: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    ai_settings: Mapped["AISettings | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    executions: Mapped[list["Execution"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class AISettings(Base):
    __tablename__ = "ai_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    encrypted_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    model: Mapped[str] = mapped_column(String(255), default="openrouter/free")

    user: Mapped[User] = relationship(back_populates="ai_settings")


class Execution(Base):
    __tablename__ = "executions"
    __table_args__ = (
        CheckConstraint("length(result) > 0", name="ck_execution_result_not_empty"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("executions.id"), nullable=True)
    tool_id: Mapped[str] = mapped_column(String(255), index=True)
    input_data: Mapped[dict[str, object]] = mapped_column(JSON)
    result: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(255))
    tone: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="executions")


class ExecutionAttempt(Base):
    __tablename__ = "execution_attempts"
    __table_args__ = (
        UniqueConstraint("user_id", "request_key", name="uq_attempt_user_request_key"),
        CheckConstraint(
            "status IN ('pending', 'complete')", name="ck_attempt_status"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    request_key: Mapped[str] = mapped_column(String(64))
    request_hash: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16), server_default=text("'pending'"))
    execution_id: Mapped[int | None] = mapped_column(
        ForeignKey("executions.id", ondelete="CASCADE"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
