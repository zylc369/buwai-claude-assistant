"""Database models for the AI conversation workspace system."""

import re
from sqlalchemy import (
    Column,
    Integer,
    Text,
    ForeignKey,
    Index,
    Boolean,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import text

Base = declarative_base()


# Directory name pattern for validation
DIRECTORY_PATTERN = re.compile(r'^[0-9a-zA-Z_-]{1,}$')


class TestMixin:
    """Mixin for test data isolation column.
    
    All models inherit from this mixin to support separating test data
    from production data in the same database.
    """
    test = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false")
    )


class Project(Base, TestMixin):
    """Project model for organizing workspaces and sessions."""

    __tablename__ = "project"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_unique_id = Column(Text, unique=True, nullable=False)
    directory = Column(Text, nullable=False)
    branch = Column(Text, nullable=True)
    name = Column(Text, nullable=False)
    gmt_create = Column(Integer, nullable=False)
    gmt_modified = Column(Integer, nullable=False)
    latest_active_time = Column(Integer, nullable=True)

    workspaces = relationship("Workspace", back_populates="project", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="project", cascade="all, delete-orphan")


class Workspace(Base, TestMixin):
    """Workspace model for project workspaces."""

    __tablename__ = "workspace"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workspace_unique_id = Column(Text, unique=True, nullable=False)
    branch = Column(Text, nullable=True)
    directory = Column(Text, nullable=False)
    extra = Column(Text, nullable=True)
    project_unique_id = Column(
        Text,
        ForeignKey("project.project_unique_id", ondelete="CASCADE"),
        nullable=False,
    )
    gmt_create = Column(Integer, nullable=False)
    gmt_modified = Column(Integer, nullable=False)
    latest_active_time = Column(Integer, nullable=True)

    project = relationship("Project", back_populates="workspaces")
    sessions = relationship("Session", back_populates="workspace", cascade="all, delete-orphan")

    __table_args__ = (
        Index("workspace_project_unique_idx", "project_unique_id"),
    )


class Session(Base, TestMixin):
    """Session model for conversation sessions."""

    __tablename__ = "session"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_unique_id = Column(Text, unique=True, nullable=False)
    external_session_id = Column(Text, nullable=False)
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


class Message(Base, TestMixin):
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


class AiResource(Base, TestMixin):
    """AI resource model for skills, commands, and system prompts."""

    __tablename__ = "ai_resource"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resource_unique_id = Column(Text, unique=True, nullable=False)
    name = Column(Text, nullable=False)
    type = Column(Text, nullable=False)
    sub_type = Column(Text, nullable=False)
    owner = Column(Text, nullable=True)
    disabled = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    content = Column(Text, nullable=False)
    gmt_create = Column(Integer, nullable=False)
    gmt_modified = Column(Integer, nullable=False)
