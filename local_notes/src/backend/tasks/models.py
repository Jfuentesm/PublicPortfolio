"""
models.py

Defines the SQLAlchemy model for task management.
This module includes the Task model and the TaskStatus enumeration.
"""

import datetime
import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum
from database.base import Base  # Shared SQLAlchemy declarative base


class TaskStatus(enum.Enum):
    """
    Enumeration for task status values.
    """
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"


class Task(Base):
    """
    Represents a task with properties such as title, description, due date,
    priority, status, recurrence rule, and an optional link to a note.
    """
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, default="")
    due_date = Column(DateTime, nullable=True)
    priority = Column(Integer, default=2)  # 1: High, 2: Medium, 3: Low
    status = Column(Enum(TaskStatus), default=TaskStatus.TODO)
    recurrence = Column(String, nullable=True)  # e.g., "daily", "weekly", "monthly"
    note_path = Column(String, nullable=True)  # Optional link to a related note
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow
    )