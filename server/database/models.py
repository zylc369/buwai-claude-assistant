"""Database models for the AI conversation workspace system."""

import re
from sqlalchemy import (
    Column,
    Integer,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# Directory name pattern for validation
DIRECTORY_PATTERN = re.compile(r'^[0-9a-zA-Z_]+$')


class Project(Base):
    """Project model for organizing workspaces and sessions."""

    __tablename__ = "project"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_unique_id = Column(Text, unique=True, nullable=False)
    directory = Column(Text, nullable=False)  # Renamed from worktree
    branch = Column(Text, nullable=True)
    name = Column(Text, nullable=True)
    time_initialized = Column(Integer, nullable=True)
    gmt_create = Column(Integer, nullable=False)  # Renamed from time_created
    gmt_modified = Column(Integer, nullable=False)  # Renamed from time_updated
    latest_active_time = Column(Integer, nullable=True)  # NEW

    workspaces = relationship("Workspace", back_populates="project", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="project", cascade="all, delete-orphan")


class Workspace(Base):
    """Workspace model for project workspaces."""

    __tablename__ = "workspace"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workspace_unique_id = Column(Text, unique=True, nullable=False)
    branch = Column(Text, nullable=True)
    name = Column(Text, nullable=True)
    directory = Column(Text, nullable=True)
    extra = Column(Text, nullable=True)
    project_unique_id = Column(
        Text,
        ForeignKey("project.project_unique_id", ondelete="CASCADE"),
        nullable=False,
    )
    gmt_create = Column(Integer, nullable=False)  # NEW
    gmt_modified = Column(Integer, nullable=False)  # NEW
    latest_active_time = Column(Integer, nullable=True)  # NEW

    project = relationship("Project", back_populates="workspaces")
    sessions = relationship("Session", back_populates="workspace", cascade="all, delete-orphan")

    __table_args__ = (
        Index("workspace_project_unique_idx", "project_unique_id"),
    )


class Session(Base):
    """Session model for conversation sessions."""

    __tablename__ = "session"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_unique_id = Column(Text, unique=True, nullable=False)
    external_session_id = Column(Text, nullable=False)
    sdk_session_id = Column(Text, nullable=True)
    project_unique_id = Column(
        Text,
        ForeignKey("project.project_unique_id", ondelete="CASCADE"),
        nullable=False,
    )
    workspace_unique_id = Column(
        Text,
        ForeignKey("workspace.workspace_unique_id"),
        nullable=False,
    )
    directory = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    gmt_create = Column(Integer, nullable=False)  # Renamed from time_created
    gmt_modified = Column(Integer, nullable=False)  # Renamed from time_updated
    time_compacting = Column(Integer, nullable=True)
    time_archived = Column(Integer, nullable=True)

    project = relationship("Project", back_populates="sessions")
    workspace = relationship("Workspace", back_populates="sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        Index("session_project_unique_idx", "project_unique_id"),
        Index("session_workspace_unique_idx", "workspace_unique_id"),
    )


class Message(Base):
    """Message model for conversation messages."""

    __tablename__ = "message"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_unique_id = Column(Text, unique=True, nullable=False)
    session_unique_id = Column(
        Text,
        ForeignKey("session.session_unique_id", ondelete="CASCADE"),
        nullable=False,
    )
    gmt_create = Column(Integer, nullable=False)  # Renamed from time_created
    gmt_modified = Column(Integer, nullable=False)  # Renamed from time_updated
    data = Column(Text, nullable=False)

    session = relationship("Session", back_populates="messages")

    __table_args__ = (
        Index("message_session_unique_idx", "session_unique_id"),
    )
