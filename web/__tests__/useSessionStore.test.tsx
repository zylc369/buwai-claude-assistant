import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useSessionStore } from '../lib/stores/useSessionStore';
import { Project, Workspace } from '../lib/api/types';

// Mock uuidv7 for deterministic test results
vi.mock('uuidv7', () => ({
  uuidv7: vi.fn(() => 'mocked-uuidv7-id'),
}));

// Helper to create mock project
function createMockProject(overrides?: Partial<Project>): Project {
  return {
    id: 1,
    project_unique_id: 'project-123',
    directory: '/project',
    branch: 'main',
    name: 'Test Project',
    gmt_create: 1234567890,
    gmt_modified: 1234567890,
    latest_active_time: null,
    ...overrides,
  };
}

// Helper to create mock workspace
function createMockWorkspace(overrides?: Partial<Workspace>): Workspace {
  return {
    id: 1,
    workspace_unique_id: 'workspace-123',
    project_unique_id: 'project-123',
    branch: 'main',
    directory: '/workspace',
    extra: null,
    gmt_create: 1234567890,
    gmt_modified: 1234567890,
    latest_active_time: null,
    ...overrides,
  };
}

describe('useSessionStore', () => {
  // Reset store state before each test
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset the store to initial state
    useSessionStore.setState({
      selectedSession: null,
      isNewSession: false,
    });
  });

  describe('createNewSession', () => {
    it('creates session with uuidv7 external_session_id', () => {
      const project = createMockProject();
      const workspace = createMockWorkspace();

      const session = useSessionStore.getState().createNewSession(project, workspace);

      expect(session.external_session_id).toBe('mocked-uuidv7-id');
      expect(session.project_unique_id).toBe(project.project_unique_id);
      expect(session.workspace_unique_id).toBe(workspace.workspace_unique_id);
      expect(session.directory).toBe(workspace.directory);
    });

    it('sets isNewSession to true', () => {
      const project = createMockProject();
      const workspace = createMockWorkspace();

      useSessionStore.getState().createNewSession(project, workspace);

      expect(useSessionStore.getState().isNewSession).toBe(true);
    });

    it('sets session_unique_id to empty string', () => {
      const project = createMockProject();
      const workspace = createMockWorkspace();

      const session = useSessionStore.getState().createNewSession(project, workspace);

      expect(session.session_unique_id).toBe('');
      expect(useSessionStore.getState().selectedSession?.session_unique_id).toBe('');
    });
  });

  describe('markSessionPersisted', () => {
    it('updates session_unique_id', () => {
      const project = createMockProject();
      const workspace = createMockWorkspace();

      // Create a new session first
      useSessionStore.getState().createNewSession(project, workspace);

      // Mark as persisted
      useSessionStore.getState().markSessionPersisted('persisted-session-id', 'Updated Title');

      expect(useSessionStore.getState().selectedSession?.session_unique_id).toBe('persisted-session-id');
    });

    it('sets isNewSession to false', () => {
      const project = createMockProject();
      const workspace = createMockWorkspace();

      // Create a new session first
      useSessionStore.getState().createNewSession(project, workspace);
      expect(useSessionStore.getState().isNewSession).toBe(true);

      // Mark as persisted
      useSessionStore.getState().markSessionPersisted('persisted-session-id', 'Updated Title');

      expect(useSessionStore.getState().isNewSession).toBe(false);
    });

    it('does not update if no selectedSession', () => {
      // Ensure no selected session
      expect(useSessionStore.getState().selectedSession).toBeNull();

      useSessionStore.getState().markSessionPersisted('persisted-session-id', 'Title');

      expect(useSessionStore.getState().selectedSession).toBeNull();
    });

    it('does not update if session already has session_unique_id', () => {
      const project = createMockProject();
      const workspace = createMockWorkspace();

      // Create a new session
      useSessionStore.getState().createNewSession(project, workspace);

      // Mark as persisted
      useSessionStore.getState().markSessionPersisted('first-session-id', 'First Title');

      // Try to mark again with different id - should not change
      useSessionStore.getState().markSessionPersisted('second-session-id', 'Second Title');

      // Should still be the first id since session already has a session_unique_id
      expect(useSessionStore.getState().selectedSession?.session_unique_id).toBe('first-session-id');
    });
  });

  describe('setSelectedSession', () => {
    it('sets isNewSession to true when session has empty session_unique_id', () => {
      const session = {
        id: 0,
        session_unique_id: '',
        external_session_id: 'ext-123',
        project_unique_id: 'project-123',
        workspace_unique_id: 'workspace-123',
        directory: '/workspace',
        title: 'New Chat',
        gmt_create: Date.now(),
        gmt_modified: Date.now(),
        time_compacting: null,
        time_archived: null,
      };

      useSessionStore.getState().setSelectedSession(session);

      expect(useSessionStore.getState().isNewSession).toBe(true);
    });

    it('sets isNewSession to false when session has session_unique_id', () => {
      const session = {
        id: 1,
        session_unique_id: 'session-123',
        external_session_id: 'ext-123',
        project_unique_id: 'project-123',
        workspace_unique_id: 'workspace-123',
        directory: '/workspace',
        title: 'Existing Chat',
        gmt_create: Date.now(),
        gmt_modified: Date.now(),
        time_compacting: null,
        time_archived: null,
      };

      useSessionStore.getState().setSelectedSession(session);

      expect(useSessionStore.getState().isNewSession).toBe(false);
    });

    it('sets isNewSession to false when session is null', () => {
      // First set a session
      const project = createMockProject();
      const workspace = createMockWorkspace();
      useSessionStore.getState().createNewSession(project, workspace);
      expect(useSessionStore.getState().isNewSession).toBe(true);

      // Then set to null
      useSessionStore.getState().setSelectedSession(null);

      expect(useSessionStore.getState().isNewSession).toBe(false);
      expect(useSessionStore.getState().selectedSession).toBeNull();
    });
  });

  describe('clearSession', () => {
    it('resets all state', () => {
      const project = createMockProject();
      const workspace = createMockWorkspace();

      // Create a session first
      useSessionStore.getState().createNewSession(project, workspace);

      // Verify state is set
      expect(useSessionStore.getState().selectedSession).not.toBeNull();
      expect(useSessionStore.getState().isNewSession).toBe(true);

      // Clear session
      useSessionStore.getState().clearSession();

      // Verify state is reset
      expect(useSessionStore.getState().selectedSession).toBeNull();
      expect(useSessionStore.getState().isNewSession).toBe(false);
    });
  });
});
