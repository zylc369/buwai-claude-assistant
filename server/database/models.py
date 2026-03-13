"""Database models for the AI conversation workspace system."""

from sqlalchemy import (
    Column,
    Integer,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Project(Base):
    """Project model for organizing workspaces and sessions."""

    __tablename__ = "project"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_unique_id = Column(Text, unique=True, nullable=False)
    worktree = Column(Text, nullable=False)
    branch = Column(Text, nullable=True)
    name = Column(Text, nullable=True)
    time_initialized = Column(Integer, nullable=True)
    time_created = Column(Integer, nullable=False)
    time_updated = Column(Integer, nullable=False)

    # Relationships
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
    extra = Column(Text, nullable=True)  # JSON data stored as text
    project_unique_id = Column(
        Text,
        ForeignKey("project.project_unique_id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    project = relationship("Project", back_populates="workspaces")
    sessions = relationship("Session", back_populates="workspace", cascade="all, delete-orphan")

    # Index
    __table_args__ = (
        Index("workspace_project_unique_idx", "project_unique_id"),
    )


class Session(Base):
    """Session model for conversation sessions."""

    __tablename__ = "session"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_unique_id = Column(Text, unique=True, nullable=False)
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
    time_created = Column(Integer, nullable=False)
    time_updated = Column(Integer, nullable=False)
    time_compacting = Column(Integer, nullable=True)
    time_archived = Column(Integer, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="sessions")
    workspace = relationship("Workspace", back_populates="sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")

    # Indexes
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
    time_created = Column(Integer, nullable=False)
    time_updated = Column(Integer, nullable=False)
    data = Column(Text, nullable=False)  # JSON data stored as text

    # Relationships
    session = relationship("Session", back_populates="messages")

    # Index
    __table_args__ = (
        Index("message_session_unique_idx", "session_unique_id"),
    )
