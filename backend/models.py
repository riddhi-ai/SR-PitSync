"""The database tables."""
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def _utc() -> datetime:
    return datetime.now(timezone.utc)


class Member(Base):
    __tablename__ = "members"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    role_text: Mapped[str] = mapped_column(String(120), default="Member")
    subsystems: Mapped[str] = mapped_column(String(120), default="")  # e.g. "chassis,aero"
    is_coordinator: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=True)
    phone: Mapped[str] = mapped_column(String(20), default="")
    branch: Mapped[str] = mapped_column(String(60), default="")
    year: Mapped[str] = mapped_column(String(4), default="")
    blood_group: Mapped[str] = mapped_column(String(4), default="")
    photo_url: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc)


class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (UniqueConstraint("member_id", "day"),)  # one row per member per day
    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"), index=True)
    day: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(10), default="present")  # present/coming/absent
    eta: Mapped[str] = mapped_column(String(5), default="")
    time_in: Mapped[str] = mapped_column(String(5), default="")
    time_out: Mapped[str] = mapped_column(String(5), default="")


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    assigned_to: Mapped[int] = mapped_column(ForeignKey("members.id"), index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("members.id"))
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="")
    due_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(12), default="todo")  # todo/in_progress/done
    progress: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc, onupdate=_utc)
    assignee: Mapped[Member] = relationship(foreign_keys=[assigned_to])


class TaskUpdate(Base):
    """A daily diary of task progress: one row per task per day."""
    __tablename__ = "task_updates"
    __table_args__ = (UniqueConstraint("task_id", "day"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    day: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(12))
    progress: Mapped[int] = mapped_column(Integer)
    notes: Mapped[str] = mapped_column(Text, default="")


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(40), primary_key=True)
    value: Mapped[str] = mapped_column(String(200))


class EmailLog(Base):
    __tablename__ = "email_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    to: Mapped[str] = mapped_column(String(120))
    subject: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    sent: Mapped[bool] = mapped_column(Boolean, default=False)
    error: Mapped[str] = mapped_column(String(300), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc)
