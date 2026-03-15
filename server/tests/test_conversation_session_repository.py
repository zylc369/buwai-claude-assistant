"""Tests for ConversationSessionRepository."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Project, Workspace, Session
from repositories.conversation_session_repository import ConversationSessionRepository
from utils.timestamp import get_timestamp_ms


# Helper function to create test project and workspace
async def create_test_project_and_workspace(
    db_session: AsyncSession,
    project_unique_id: str,
    workspace_unique_id: str,
) -> tuple[Project, Workspace]:
    """Create a test project and workspace for sessions."""
    current_time = get_timestamp_ms()
    
    project = Project(
        project_unique_id=project_unique_id,
        directory="worktree",
        name=f"Project {project_unique_id}",
        gmt_create=current_time,
        gmt_modified=current_time,
            test=True,
        )
    db_session.add(project)
    await db_session.flush()
    
    workspace = Workspace(
        workspace_unique_id=workspace_unique_id,
        project_unique_id=project_unique_id,
        directory="test-dir",
        gmt_create=current_time,
        gmt_modified=current_time,
            test=True,
        )
    db_session.add(workspace)
    await db_session.flush()
    
    return project, workspace


# Helper function to create test sessions
async def create_test_session(
    repo: ConversationSessionRepository,
    session_unique_id: str,
    project_unique_id: str,
    workspace_unique_id: str,
    title: str = None,
    directory: str = "/test/dir",
    time_archived: int = None,
) -> Session:
    """Create a test session."""
    current_time = get_timestamp_ms()
    return await repo.create(
        session_unique_id=session_unique_id,
        external_session_id=f"external-{session_unique_id}",
        project_unique_id=project_unique_id,
        workspace_unique_id=workspace_unique_id,
        directory=directory,
        title=title or f"Session {session_unique_id}",
        gmt_create=current_time,
        gmt_modified=current_time,
        time_archived=time_archived,
        test=True,
    )


class TestConversationSessionRepositoryCreate:
    """Tests for ConversationSessionRepository.create method."""

    @pytest.mark.asyncio
    async def test_create_session(self, db_session: AsyncSession):
        """Test creating a session."""
        project, workspace = await create_test_project_and_workspace(
            db_session,
            project_unique_id="proj-001",
            workspace_unique_id="ws-001",
        )
        repo = ConversationSessionRepository(db_session)
        
        session = await create_test_session(
            repo,
            session_unique_id="sess-001",
            project_unique_id="proj-001",
            workspace_unique_id="ws-001",
            title="Test Session",
        )
        await db_session.commit()
        
        assert session.id is not None
        assert session.session_unique_id == "sess-001"
        assert session.project_unique_id == "proj-001"
        assert session.workspace_unique_id == "ws-001"
        assert session.title == "Test Session"
        assert session.directory == "/test/dir"

    @pytest.mark.asyncio
    async def test_create_session_with_archived_time(self, db_session: AsyncSession):
        """Test creating a session with archived time."""
        project, workspace = await create_test_project_and_workspace(
            db_session,
            project_unique_id="proj-002",
            workspace_unique_id="ws-002",
        )
        repo = ConversationSessionRepository(db_session)
        
        archived_time = get_timestamp_ms()
        session = await create_test_session(
            repo,
            session_unique_id="sess-002",
            project_unique_id="proj-002",
            workspace_unique_id="ws-002",
            time_archived=archived_time,
        )
        await db_session.commit()
        
        assert session.time_archived == archived_time


class TestConversationSessionRepositoryGetById:
    """Tests for ConversationSessionRepository.get_by_id method."""

    @pytest.mark.asyncio
    async def test_get_by_id_exists(self, db_session: AsyncSession):
        """Test getting an existing session by ID."""
        project, workspace = await create_test_project_and_workspace(
            db_session,
            project_unique_id="proj-003",
            workspace_unique_id="ws-003",
        )
        repo = ConversationSessionRepository(db_session)
        
        session = await create_test_session(
            repo,
            session_unique_id="sess-003",
            project_unique_id="proj-003",
            workspace_unique_id="ws-003",
            title="Find By ID",
        )
        await db_session.commit()
        
        result = await repo.get_by_id(session.id, test=True)
        
        assert result is not None
        assert result.id == session.id
        assert result.session_unique_id == "sess-003"
        assert result.title == "Find By ID"

    @pytest.mark.asyncio
    async def test_get_by_id_not_exists(self, db_session: AsyncSession):
        """Test getting a non-existent session by ID."""
        repo = ConversationSessionRepository(db_session)
        
        result = await repo.get_by_id(99999, test=True)
        
        assert result is None


class TestConversationSessionRepositoryGetByUniqueId:
    """Tests for ConversationSessionRepository.get_by_unique_id method."""

    @pytest.mark.asyncio
    async def test_get_by_unique_id_exists(self, db_session: AsyncSession):
        """Test getting an existing session by unique ID."""
        project, workspace = await create_test_project_and_workspace(
            db_session,
            project_unique_id="proj-004",
            workspace_unique_id="ws-004",
        )
        repo = ConversationSessionRepository(db_session)
        
        session = await create_test_session(
            repo,
            session_unique_id="unique-sess-001",
            project_unique_id="proj-004",
            workspace_unique_id="ws-004",
            title="Unique Session",
        )
        await db_session.commit()
        
        result = await repo.get_by_unique_id("unique-sess-001", test=True)
        
        assert result is not None
        assert result.session_unique_id == "unique-sess-001"
        assert result.title == "Unique Session"

    @pytest.mark.asyncio
    async def test_get_by_unique_id_not_exists(self, db_session: AsyncSession):
        """Test getting a non-existent session by unique ID."""
        repo = ConversationSessionRepository(db_session)
        
        result = await repo.get_by_unique_id("non-existent-unique-id", test=True)
        
        assert result is None


class TestConversationSessionRepositoryGetByProjectUniqueId:
    """Tests for ConversationSessionRepository.get_by_project_unique_id method."""

    @pytest.mark.asyncio
    async def test_get_by_project_unique_id(self, db_session: AsyncSession):
        """Test getting sessions by project unique ID."""
        project, workspace = await create_test_project_and_workspace(
            db_session,
            project_unique_id="proj-005",
            workspace_unique_id="ws-005",
        )
        repo = ConversationSessionRepository(db_session)
        
        # Create multiple sessions for the project
        for i in range(3):
            await create_test_session(
                repo,
                session_unique_id=f"sess-proj-{i:03d}",
                project_unique_id="proj-005",
                workspace_unique_id="ws-005",
            )
        await db_session.commit()
        
        results = await repo.get_by_project_unique_id("proj-005", test=True)
        
        assert len(results) == 3
        for session in results:
            assert session.project_unique_id == "proj-005"

    @pytest.mark.asyncio
    async def test_get_by_project_unique_id_with_pagination(self, db_session: AsyncSession):
        """Test getting sessions by project unique ID with pagination."""
        project, workspace = await create_test_project_and_workspace(
            db_session,
            project_unique_id="proj-006",
            workspace_unique_id="ws-006",
        )
        repo = ConversationSessionRepository(db_session)
        
        # Create multiple sessions
        for i in range(10):
            await create_test_session(
                repo,
                session_unique_id=f"sess-page-{i:03d}",
                project_unique_id="proj-006",
                workspace_unique_id="ws-006",
            )
        await db_session.commit()
        
        # Get first page
        page1 = await repo.get_by_project_unique_id("proj-006", offset=0, limit=3, test=True)
        assert len(page1) == 3
        
        # Get second page
        page2 = await repo.get_by_project_unique_id("proj-006", offset=3, limit=3, test=True)
        assert len(page2) == 3
        
        # Get last page
        last_page = await repo.get_by_project_unique_id("proj-006", offset=9, limit=3, test=True)
        assert len(last_page) == 1

    @pytest.mark.asyncio
    async def test_get_by_project_unique_id_exclude_archived(self, db_session: AsyncSession):
        """Test getting sessions excluding archived ones."""
        project, workspace = await create_test_project_and_workspace(
            db_session,
            project_unique_id="proj-007",
            workspace_unique_id="ws-007",
        )
        repo = ConversationSessionRepository(db_session)
        
        # Create active sessions
        for i in range(3):
            await create_test_session(
                repo,
                session_unique_id=f"sess-active-{i:03d}",
                project_unique_id="proj-007",
                workspace_unique_id="ws-007",
            )
        
        # Create archived sessions
        archived_time = get_timestamp_ms()
        for i in range(2):
            await create_test_session(
                repo,
                session_unique_id=f"sess-archived-{i:03d}",
                project_unique_id="proj-007",
                workspace_unique_id="ws-007",
                time_archived=archived_time,
            )
        await db_session.commit()
        
        # Get only active sessions (default)
        active_only = await repo.get_by_project_unique_id(
            "proj-007", include_archived=False, test=True
        )
        assert len(active_only) == 3
        
        # Get all sessions including archived
        all_sessions = await repo.get_by_project_unique_id(
            "proj-007", include_archived=True, test=True
        )
        assert len(all_sessions) == 5

    @pytest.mark.asyncio
    async def test_get_by_project_unique_id_empty(self, db_session: AsyncSession):
        """Test getting sessions for a project with no sessions."""
        project, workspace = await create_test_project_and_workspace(
            db_session,
            project_unique_id="proj-empty",
            workspace_unique_id="ws-empty",
        )
        repo = ConversationSessionRepository(db_session)
        
        results = await repo.get_by_project_unique_id("proj-empty", test=True)
        
        assert len(results) == 0


class TestConversationSessionRepositoryGetByWorkspaceUniqueId:
    """Tests for ConversationSessionRepository.get_by_workspace_unique_id method."""

    @pytest.mark.asyncio
    async def test_get_by_workspace_unique_id(self, db_session: AsyncSession):
        """Test getting sessions by workspace unique ID."""
        project, workspace = await create_test_project_and_workspace(
            db_session,
            project_unique_id="proj-008",
            workspace_unique_id="ws-008",
        )
        repo = ConversationSessionRepository(db_session)
        
        # Create multiple sessions for the workspace
        for i in range(3):
            await create_test_session(
                repo,
                session_unique_id=f"sess-ws-{i:03d}",
                project_unique_id="proj-008",
                workspace_unique_id="ws-008",
            )
        await db_session.commit()
        
        results = await repo.get_by_workspace_unique_id("ws-008", test=True)
        
        assert len(results) == 3
        for session in results:
            assert session.workspace_unique_id == "ws-008"

    @pytest.mark.asyncio
    async def test_get_by_workspace_unique_id_with_pagination(self, db_session: AsyncSession):
        """Test getting sessions by workspace unique ID with pagination."""
        project, workspace = await create_test_project_and_workspace(
            db_session,
            project_unique_id="proj-009",
            workspace_unique_id="ws-009",
        )
        repo = ConversationSessionRepository(db_session)
        
        # Create multiple sessions
        for i in range(10):
            await create_test_session(
                repo,
                session_unique_id=f"sess-wspage-{i:03d}",
                project_unique_id="proj-009",
                workspace_unique_id="ws-009",
            )
        await db_session.commit()
        
        # Get first page
        page1 = await repo.get_by_workspace_unique_id("ws-009", offset=0, limit=3, test=True)
        assert len(page1) == 3
        
        # Get second page
        page2 = await repo.get_by_workspace_unique_id("ws-009", offset=3, limit=3, test=True)
        assert len(page2) == 3

    @pytest.mark.asyncio
    async def test_get_by_workspace_unique_id_exclude_archived(self, db_session: AsyncSession):
        """Test getting sessions excluding archived ones."""
        project, workspace = await create_test_project_and_workspace(
            db_session,
            project_unique_id="proj-010",
            workspace_unique_id="ws-010",
        )
        repo = ConversationSessionRepository(db_session)
        
        # Create active sessions
        for i in range(3):
            await create_test_session(
                repo,
                session_unique_id=f"sess-ws-active-{i:03d}",
                project_unique_id="proj-010",
                workspace_unique_id="ws-010",
            )
        
        # Create archived sessions
        archived_time = get_timestamp_ms()
        for i in range(2):
            await create_test_session(
                repo,
                session_unique_id=f"sess-ws-archived-{i:03d}",
                project_unique_id="proj-010",
                workspace_unique_id="ws-010",
                time_archived=archived_time,
            )
        await db_session.commit()
        
        # Get only active sessions (default)
        active_only = await repo.get_by_workspace_unique_id(
            "ws-010", include_archived=False, test=True
        )
        assert len(active_only) == 3
        
        # Get all sessions including archived
        all_sessions = await repo.get_by_workspace_unique_id(
            "ws-010", include_archived=True, test=True
        )
        assert len(all_sessions) == 5

    @pytest.mark.asyncio
    async def test_get_by_workspace_unique_id_empty(self, db_session: AsyncSession):
        """Test getting sessions for a workspace with no sessions."""
        project, workspace = await create_test_project_and_workspace(
            db_session,
            project_unique_id="proj-ws-empty",
            workspace_unique_id="ws-empty",
        )
        repo = ConversationSessionRepository(db_session)
        
        results = await repo.get_by_workspace_unique_id("ws-empty", test=True)
        
        assert len(results) == 0


class TestConversationSessionRepositoryList:
    """Tests for ConversationSessionRepository.list method."""

    @pytest.mark.asyncio
    async def test_list_all_sessions(self, db_session: AsyncSession):
        """Test listing all sessions."""
        project, workspace = await create_test_project_and_workspace(
            db_session,
            project_unique_id="proj-011",
            workspace_unique_id="ws-011",
        )
        repo = ConversationSessionRepository(db_session)
        
        for i in range(5):
            await create_test_session(
                repo,
                session_unique_id=f"sess-list-{i:03d}",
                project_unique_id="proj-011",
                workspace_unique_id="ws-011",
            )
        await db_session.commit()
        
        results = await repo.list(test=True)
        
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_list_with_pagination(self, db_session: AsyncSession):
        """Test listing sessions with pagination."""
        project, workspace = await create_test_project_and_workspace(
            db_session,
            project_unique_id="proj-012",
            workspace_unique_id="ws-012",
        )
        repo = ConversationSessionRepository(db_session)
        
        for i in range(10):
            await create_test_session(
                repo,
                session_unique_id=f"sess-listpage-{i:03d}",
                project_unique_id="proj-012",
                workspace_unique_id="ws-012",
            )
        await db_session.commit()
        
        # Get first page
        page1 = await repo.list(offset=0, limit=3, test=True)
        assert len(page1) == 3
        
        # Get second page
        page2 = await repo.list(offset=3, limit=3, test=True)
        assert len(page2) == 3
        
        # Get last page
        last_page = await repo.list(offset=9, limit=3, test=True)
        assert len(last_page) == 1

    @pytest.mark.asyncio
    async def test_list_with_project_filter(self, db_session: AsyncSession):
        """Test listing sessions filtered by project."""
        # Create two projects
        project1, workspace1 = await create_test_project_and_workspace(
            db_session,
            project_unique_id="proj-filter-001",
            workspace_unique_id="ws-filter-001",
        )
        project2, workspace2 = await create_test_project_and_workspace(
            db_session,
            project_unique_id="proj-filter-002",
            workspace_unique_id="ws-filter-002",
        )
        repo = ConversationSessionRepository(db_session)
        
        # Create sessions for project 1
        for i in range(3):
            await create_test_session(
                repo,
                session_unique_id=f"sess-filter1-{i:03d}",
                project_unique_id="proj-filter-001",
                workspace_unique_id="ws-filter-001",
            )
        
        # Create sessions for project 2
        for i in range(2):
            await create_test_session(
                repo,
                session_unique_id=f"sess-filter2-{i:03d}",
                project_unique_id="proj-filter-002",
                workspace_unique_id="ws-filter-002",
            )
        await db_session.commit()
        
        # Filter by project 1
        results = await repo.list(project_unique_id="proj-filter-001", test=True)
        assert len(results) == 3
        
        # Filter by project 2
        results = await repo.list(project_unique_id="proj-filter-002", test=True)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_list_with_workspace_filter(self, db_session: AsyncSession):
        """Test listing sessions filtered by workspace."""
        project, _ = await create_test_project_and_workspace(
            db_session,
            project_unique_id="proj-ws-filter",
            workspace_unique_id="ws-ws-filter-001",
        )
        # Create another workspace for the same project
        current_time = get_timestamp_ms()
        workspace2 = Workspace(
            workspace_unique_id="ws-ws-filter-002",
            project_unique_id="proj-ws-filter",
            directory="test-dir2",
            gmt_create=current_time,
            gmt_modified=current_time,
            test=True,
        )
        db_session.add(workspace2)
        await db_session.flush()
        
        repo = ConversationSessionRepository(db_session)
        
        # Create sessions for workspace 1
        for i in range(3):
            await create_test_session(
                repo,
                session_unique_id=f"sess-wsf1-{i:03d}",
                project_unique_id="proj-ws-filter",
                workspace_unique_id="ws-ws-filter-001",
            )
        
        # Create sessions for workspace 2
        for i in range(2):
            await create_test_session(
                repo,
                session_unique_id=f"sess-wsf2-{i:03d}",
                project_unique_id="proj-ws-filter",
                workspace_unique_id="ws-ws-filter-002",
            )
        await db_session.commit()
        
        # Filter by workspace 1
        results = await repo.list(workspace_unique_id="ws-ws-filter-001", test=True)
        assert len(results) == 3
        
        # Filter by workspace 2
        results = await repo.list(workspace_unique_id="ws-ws-filter-002", test=True)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_list_exclude_archived(self, db_session: AsyncSession):
        """Test listing sessions excluding archived ones."""
        project, workspace = await create_test_project_and_workspace(
            db_session,
            project_unique_id="proj-list-archive",
            workspace_unique_id="ws-list-archive",
        )
        repo = ConversationSessionRepository(db_session)
        
        # Create active sessions
        for i in range(3):
            await create_test_session(
                repo,
                session_unique_id=f"sess-list-active-{i:03d}",
                project_unique_id="proj-list-archive",
                workspace_unique_id="ws-list-archive",
            )
        
        # Create archived sessions
        archived_time = get_timestamp_ms()
        for i in range(2):
            await create_test_session(
                repo,
                session_unique_id=f"sess-list-archived-{i:03d}",
                project_unique_id="proj-list-archive",
                workspace_unique_id="ws-list-archive",
                time_archived=archived_time,
            )
        await db_session.commit()
        
        # List only active sessions (default)
        active_only = await repo.list(include_archived=False, test=True)
        assert len(active_only) == 3
        
        # List all sessions including archived
        all_sessions = await repo.list(include_archived=True, test=True)
        assert len(all_sessions) == 5


class TestConversationSessionRepositoryArchive:
    """Tests for ConversationSessionRepository.archive method."""

    @pytest.mark.asyncio
    async def test_archive_session(self, db_session: AsyncSession):
        """Test archiving a session."""
        project, workspace = await create_test_project_and_workspace(
            db_session,
            project_unique_id="proj-archive",
            workspace_unique_id="ws-archive",
        )
        repo = ConversationSessionRepository(db_session)
        
        session = await create_test_session(
            repo,
            session_unique_id="sess-archive",
            project_unique_id="proj-archive",
            workspace_unique_id="ws-archive",
        )
        await db_session.commit()
        
        assert session.time_archived is None
        
        # Archive the session
        archived = await repo.archive("sess-archive", test=True)
        await db_session.commit()
        
        assert archived is not None
        assert archived.time_archived is not None
        assert archived.session_unique_id == "sess-archive"

    @pytest.mark.asyncio
    async def test_archive_session_with_custom_time(self, db_session: AsyncSession):
        """Test archiving a session with custom timestamp."""
        project, workspace = await create_test_project_and_workspace(
            db_session,
            project_unique_id="proj-archive-custom",
            workspace_unique_id="ws-archive-custom",
        )
        repo = ConversationSessionRepository(db_session)
        
        session = await create_test_session(
            repo,
            session_unique_id="sess-archive-custom",
            project_unique_id="proj-archive-custom",
            workspace_unique_id="ws-archive-custom",
        )
        await db_session.commit()
        
        custom_time = 1700000000
        archived = await repo.archive("sess-archive-custom", archived_time=custom_time, test=True)
        await db_session.commit()
        
        assert archived.time_archived == custom_time

    @pytest.mark.asyncio
    async def test_archive_non_existent_session(self, db_session: AsyncSession):
        """Test archiving a non-existent session."""
        repo = ConversationSessionRepository(db_session)
        
        result = await repo.archive("non-existent-session", test=True)
        
        assert result is None


class TestConversationSessionRepositoryUnarchive:
    """Tests for ConversationSessionRepository.unarchive method."""

    @pytest.mark.asyncio
    async def test_unarchive_session(self, db_session: AsyncSession):
        """Test unarchiving a session."""
        project, workspace = await create_test_project_and_workspace(
            db_session,
            project_unique_id="proj-unarchive",
            workspace_unique_id="ws-unarchive",
        )
        repo = ConversationSessionRepository(db_session)
        
        archived_time = get_timestamp_ms()
        session = await create_test_session(
            repo,
            session_unique_id="sess-unarchive",
            project_unique_id="proj-unarchive",
            workspace_unique_id="ws-unarchive",
            time_archived=archived_time,
        )
        await db_session.commit()
        
        assert session.time_archived is not None
        
        # Unarchive the session
        unarchived = await repo.unarchive("sess-unarchive", test=True)
        await db_session.commit()
        
        assert unarchived is not None
        assert unarchived.time_archived is None
        assert unarchived.session_unique_id == "sess-unarchive"

    @pytest.mark.asyncio
    async def test_unarchive_non_existent_session(self, db_session: AsyncSession):
        """Test unarchiving a non-existent session."""
        repo = ConversationSessionRepository(db_session)
        
        result = await repo.unarchive("non-existent-session", test=True)
        
        assert result is None


class TestConversationSessionRepositoryCountByProject:
    """Tests for ConversationSessionRepository.count_by_project method."""

    @pytest.mark.asyncio
    async def test_count_by_project(self, db_session: AsyncSession):
        """Test counting sessions by project."""
        project, workspace = await create_test_project_and_workspace(
            db_session,
            project_unique_id="proj-count",
            workspace_unique_id="ws-count",
        )
        repo = ConversationSessionRepository(db_session)
        
        for i in range(5):
            await create_test_session(
                repo,
                session_unique_id=f"sess-count-{i:03d}",
                project_unique_id="proj-count",
                workspace_unique_id="ws-count",
            )
        await db_session.commit()
        
        count = await repo.count_by_project("proj-count", test=True)
        
        assert count == 5

    @pytest.mark.asyncio
    async def test_count_by_project_exclude_archived(self, db_session: AsyncSession):
        """Test counting sessions by project excluding archived."""
        project, workspace = await create_test_project_and_workspace(
            db_session,
            project_unique_id="proj-count-archive",
            workspace_unique_id="ws-count-archive",
        )
        repo = ConversationSessionRepository(db_session)
        
        # Create active sessions
        for i in range(3):
            await create_test_session(
                repo,
                session_unique_id=f"sess-count-active-{i:03d}",
                project_unique_id="proj-count-archive",
                workspace_unique_id="ws-count-archive",
            )
        
        # Create archived sessions
        archived_time = get_timestamp_ms()
        for i in range(2):
            await create_test_session(
                repo,
                session_unique_id=f"sess-count-archived-{i:03d}",
                project_unique_id="proj-count-archive",
                workspace_unique_id="ws-count-archive",
                time_archived=archived_time,
            )
        await db_session.commit()
        
        # Count only active sessions (default)
        active_count = await repo.count_by_project("proj-count-archive", include_archived=False, test=True)
        assert active_count == 3
        
        # Count all sessions including archived
        total_count = await repo.count_by_project("proj-count-archive", include_archived=True, test=True)
        assert total_count == 5

    @pytest.mark.asyncio
    async def test_count_by_project_empty(self, db_session: AsyncSession):
        """Test counting sessions for a project with no sessions."""
        project, workspace = await create_test_project_and_workspace(
            db_session,
            project_unique_id="proj-count-empty",
            workspace_unique_id="ws-count-empty",
        )
        repo = ConversationSessionRepository(db_session)
        
        count = await repo.count_by_project("proj-count-empty", test=True)
        
        assert count == 0


class TestConversationSessionRepositoryCountByWorkspace:
    """Tests for ConversationSessionRepository.count_by_workspace method."""

    @pytest.mark.asyncio
    async def test_count_by_workspace(self, db_session: AsyncSession):
        """Test counting sessions by workspace."""
        project, workspace = await create_test_project_and_workspace(
            db_session,
            project_unique_id="proj-ws-count",
            workspace_unique_id="ws-ws-count",
        )
        repo = ConversationSessionRepository(db_session)
        
        for i in range(5):
            await create_test_session(
                repo,
                session_unique_id=f"sess-ws-count-{i:03d}",
                project_unique_id="proj-ws-count",
                workspace_unique_id="ws-ws-count",
            )
        await db_session.commit()
        
        count = await repo.count_by_workspace("ws-ws-count", test=True)
        
        assert count == 5

    @pytest.mark.asyncio
    async def test_count_by_workspace_exclude_archived(self, db_session: AsyncSession):
        """Test counting sessions by workspace excluding archived."""
        project, workspace = await create_test_project_and_workspace(
            db_session,
            project_unique_id="proj-ws-count-archive",
            workspace_unique_id="ws-ws-count-archive",
        )
        repo = ConversationSessionRepository(db_session)
        
        # Create active sessions
        for i in range(3):
            await create_test_session(
                repo,
                session_unique_id=f"sess-ws-count-active-{i:03d}",
                project_unique_id="proj-ws-count-archive",
                workspace_unique_id="ws-ws-count-archive",
            )
        
        # Create archived sessions
        archived_time = get_timestamp_ms()
        for i in range(2):
            await create_test_session(
                repo,
                session_unique_id=f"sess-ws-count-archived-{i:03d}",
                project_unique_id="proj-ws-count-archive",
                workspace_unique_id="ws-ws-count-archive",
                time_archived=archived_time,
            )
        await db_session.commit()
        
        # Count only active sessions (default)
        active_count = await repo.count_by_workspace("ws-ws-count-archive", include_archived=False, test=True)
        assert active_count == 3
        
        # Count all sessions including archived
        total_count = await repo.count_by_workspace("ws-ws-count-archive", include_archived=True, test=True)
        assert total_count == 5


class TestConversationSessionRepositoryUpdate:
    """Tests for ConversationSessionRepository.update method."""

    @pytest.mark.asyncio
    async def test_update_session_title(self, db_session: AsyncSession):
        """Test updating session title."""
        project, workspace = await create_test_project_and_workspace(
            db_session,
            project_unique_id="proj-update",
            workspace_unique_id="ws-update",
        )
        repo = ConversationSessionRepository(db_session)
        
        session = await create_test_session(
            repo,
            session_unique_id="sess-update",
            project_unique_id="proj-update",
            workspace_unique_id="ws-update",
            title="Original Title",
        )
        await db_session.commit()
        
        updated = await repo.update(session, title="Updated Title", test=True)
        await db_session.commit()
        
        assert updated.title == "Updated Title"
        assert updated.session_unique_id == "sess-update"

    @pytest.mark.asyncio
    async def test_update_multiple_fields(self, db_session: AsyncSession):
        """Test updating multiple session fields."""
        project, workspace = await create_test_project_and_workspace(
            db_session,
            project_unique_id="proj-update-multi",
            workspace_unique_id="ws-update-multi",
        )
        repo = ConversationSessionRepository(db_session)
        
        session = await create_test_session(
            repo,
            session_unique_id="sess-update-multi",
            project_unique_id="proj-update-multi",
            workspace_unique_id="ws-update-multi",
            title="Original",
            directory="original-path",
        )
        await db_session.commit()
        
        new_time = get_timestamp_ms() + 1000
        updated = await repo.update(
            session,
            title="Updated",
            directory="new-path",
            gmt_modified=new_time,
            test=True,
        )
        await db_session.commit()
        
        assert updated.title == "Updated"
        assert updated.directory == "new-path"
        assert updated.gmt_modified == new_time


class TestConversationSessionRepositoryDelete:
    """Tests for ConversationSessionRepository.delete method."""

    @pytest.mark.asyncio
    async def test_delete_session(self, db_session: AsyncSession):
        """Test deleting a session."""
        project, workspace = await create_test_project_and_workspace(
            db_session,
            project_unique_id="proj-delete",
            workspace_unique_id="ws-delete",
        )
        repo = ConversationSessionRepository(db_session)
        
        session = await create_test_session(
            repo,
            session_unique_id="sess-delete",
            project_unique_id="proj-delete",
            workspace_unique_id="ws-delete",
            title="To Delete",
        )
        await db_session.commit()
        session_id = session.id
        
        await repo.delete(session)
        await db_session.commit()
        
        result = await repo.get_by_id(session_id, test=True)
        assert result is None


class TestConversationSessionRepositoryExists:
    """Tests for ConversationSessionRepository.exists method."""

    @pytest.mark.asyncio
    async def test_exists_true(self, db_session: AsyncSession):
        """Test checking if session exists (True case)."""
        project, workspace = await create_test_project_and_workspace(
            db_session,
            project_unique_id="proj-exists",
            workspace_unique_id="ws-exists",
        )
        repo = ConversationSessionRepository(db_session)
        
        session = await create_test_session(
            repo,
            session_unique_id="sess-exists",
            project_unique_id="proj-exists",
            workspace_unique_id="ws-exists",
        )
        await db_session.commit()
        
        assert await repo.exists(session.id, test=True) is True

    @pytest.mark.asyncio
    async def test_exists_false(self, db_session: AsyncSession):
        """Test checking if session exists (False case)."""
        repo = ConversationSessionRepository(db_session)
        
        assert await repo.exists(99999, test=True) is False


class TestConversationSessionRepositoryGetByExternalSessionId:
    """Tests for ConversationSessionRepository.get_by_external_session_id method."""

    @pytest.mark.asyncio
    async def test_get_by_external_session_id_found(self, db_session: AsyncSession):
        """Test getting an existing session by external_session_id."""
        project, workspace = await create_test_project_and_workspace(
            db_session,
            project_unique_id="proj-ext-001",
            workspace_unique_id="ws-ext-001",
        )
        repo = ConversationSessionRepository(db_session)
        
        session = await create_test_session(
            repo,
            session_unique_id="sess-ext-001",
            project_unique_id="proj-ext-001",
            workspace_unique_id="ws-ext-001",
            title="External Session",
        )
        await db_session.commit()
        
        result = await repo.get_by_external_session_id("external-sess-ext-001", test=True)
        
        assert result is not None
        assert result.session_unique_id == "sess-ext-001"
        assert result.external_session_id == "external-sess-ext-001"
        assert result.title == "External Session"

    @pytest.mark.asyncio
    async def test_get_by_external_session_id_not_found(self, db_session: AsyncSession):
        """Test getting a non-existent session by external_session_id."""
        repo = ConversationSessionRepository(db_session)
        
        result = await repo.get_by_external_session_id("non-existent-external-id", test=True)
        
        assert result is None


class TestConversationSessionRepositoryCreateWithSdkSessionId:
    """Tests for creating sessions with sdk_session_id."""

    @pytest.mark.asyncio
    async def test_create_session_with_sdk_session_id(self, db_session: AsyncSession):
        """Test creating a session with sdk_session_id."""
        project, workspace = await create_test_project_and_workspace(
            db_session,
            project_unique_id="proj-sdk-001",
            workspace_unique_id="ws-sdk-001",
        )
        repo = ConversationSessionRepository(db_session)
        
        current_time = get_timestamp_ms()
        session = await repo.create_session(
            session_unique_id="sess-sdk-001",
            external_session_id="external-sess-sdk-001",
            project_unique_id="proj-sdk-001",
            workspace_unique_id="ws-sdk-001",
            directory="test-sdk-dir",
            title="SDK Session",
            sdk_session_id="sdk-session-12345",
            gmt_create=current_time,
            gmt_modified=current_time,
            test=True,
        )
        await db_session.commit()
        
        assert session.id is not None
        assert session.session_unique_id == "sess-sdk-001"
        assert session.external_session_id == "external-sess-sdk-001"
        assert session.sdk_session_id == "sdk-session-12345"
        assert session.title == "SDK Session"


class TestConversationSessionRepositoryUpdateSdkSessionId:
    """Tests for updating sdk_session_id."""

    @pytest.mark.asyncio
    async def test_update_session_sdk_session_id(self, db_session: AsyncSession):
        """Test updating sdk_session_id for an existing session."""
        project, workspace = await create_test_project_and_workspace(
            db_session,
            project_unique_id="proj-sdk-update",
            workspace_unique_id="ws-sdk-update",
        )
        repo = ConversationSessionRepository(db_session)
        
        session = await create_test_session(
            repo,
            session_unique_id="sess-sdk-update",
            project_unique_id="proj-sdk-update",
            workspace_unique_id="ws-sdk-update",
            title="SDK Update Session",
        )
        await db_session.commit()
        
        assert session.sdk_session_id is None
        
        updated = await repo.update_session(
            session,
            sdk_session_id="new-sdk-session-67890",
            test=True,
        )
        await db_session.commit()
        
        assert updated.sdk_session_id == "new-sdk-session-67890"
        assert updated.session_unique_id == "sess-sdk-update"
