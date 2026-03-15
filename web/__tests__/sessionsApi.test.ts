import { describe, it, expect, vi, beforeEach } from 'vitest';
import { sessionsApi } from '../lib/api/sessions';
import { api } from '../lib/api/client';
import { Session, CreateSessionRequest, ListSessionsParams } from '../lib/api/types';

// Mock the api client
vi.mock('../lib/api/client', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('sessionsApi', () => {
  const mockApi = vi.mocked(api);

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('list', () => {
    it('should call api.get with correct URL and query params', async () => {
      const mockSessions: Session[] = [
        {
          id: 1,
          session_unique_id: 'session-1',
          external_session_id: 'ext-1',
          project_unique_id: 'project-1',
          workspace_unique_id: 'workspace-1',
          directory: '/workspace',
          title: 'Test Session',
          gmt_create: 1234567890,
          gmt_modified: 1234567890,
          time_compacting: null,
          time_archived: null,
        },
      ];

      mockApi.get.mockResolvedValueOnce(mockSessions);

      const params: ListSessionsParams = {
        project_unique_id: 'project-1',
        workspace_unique_id: 'workspace-1',
      };

      const result = await sessionsApi.list(params);

      expect(mockApi.get).toHaveBeenCalledWith('/sessions/?project_unique_id=project-1&workspace_unique_id=workspace-1');
      expect(result).toEqual(mockSessions);
    });

    it('should include optional params in query string', async () => {
      const mockSessions: Session[] = [];

      mockApi.get.mockResolvedValueOnce(mockSessions);

      const params: ListSessionsParams = {
        project_unique_id: 'project-1',
        workspace_unique_id: 'workspace-1',
        offset: 10,
        limit: 5,
        include_archived: true,
      };

      await sessionsApi.list(params);

      expect(mockApi.get).toHaveBeenCalledWith(
        expect.stringContaining('project_unique_id=project-1')
      );
      expect(mockApi.get).toHaveBeenCalledWith(
        expect.stringContaining('workspace_unique_id=workspace-1')
      );
      expect(mockApi.get).toHaveBeenCalledWith(
        expect.stringContaining('offset=10')
      );
      expect(mockApi.get).toHaveBeenCalledWith(
        expect.stringContaining('limit=5')
      );
      expect(mockApi.get).toHaveBeenCalledWith(
        expect.stringContaining('include_archived=true')
      );
    });

    it('should return base URL when no optional params provided', async () => {
      mockApi.get.mockResolvedValueOnce([]);

      const params: ListSessionsParams = {
        project_unique_id: 'project-1',
        workspace_unique_id: 'workspace-1',
      };

      await sessionsApi.list(params);

      expect(mockApi.get).toHaveBeenCalledWith(
        expect.not.stringContaining('offset')
      );
    });
  });

  describe('get', () => {
    it('should call api.get with correct URL for session unique id', async () => {
      const mockSession: Session = {
        id: 1,
        session_unique_id: 'session-123',
        external_session_id: 'ext-123',
        project_unique_id: 'project-1',
        workspace_unique_id: 'workspace-1',
        directory: '/workspace',
        title: 'Test Session',
        gmt_create: 1234567890,
        gmt_modified: 1234567890,
        time_compacting: null,
        time_archived: null,
      };

      mockApi.get.mockResolvedValueOnce(mockSession);

      const result = await sessionsApi.get('session-123');

      expect(mockApi.get).toHaveBeenCalledWith('/sessions/session-123');
      expect(result).toEqual(mockSession);
    });

    it('should propagate errors from api.get', async () => {
      const error = new Error('Session not found');
      mockApi.get.mockRejectedValueOnce(error);

      await expect(sessionsApi.get('nonexistent')).rejects.toThrow('Session not found');
    });
  });

  describe('create', () => {
    it('should call api.post with correct URL and data', async () => {
      const createData: CreateSessionRequest = {
        session_unique_id: 'new-session',
        external_session_id: 'ext-new-session',
        project_unique_id: 'project-1',
        workspace_unique_id: 'workspace-1',
        directory: '/workspace',
        title: 'New Session',
      };

      const mockCreatedSession: Session = {
        id: 2,
        ...createData,
        gmt_create: 1234567891,
        gmt_modified: 1234567891,
        time_compacting: null,
        time_archived: null,
      };

      mockApi.post.mockResolvedValueOnce(mockCreatedSession);

      const result = await sessionsApi.create(createData);

      expect(mockApi.post).toHaveBeenCalledWith('/sessions/', createData);
      expect(result).toEqual(mockCreatedSession);
      expect(result.external_session_id).toBe('ext-new-session');
    });

    it('should propagate validation errors from api.post', async () => {
      const createData: CreateSessionRequest = {
        session_unique_id: '',
        external_session_id: '',
        project_unique_id: 'project-1',
        workspace_unique_id: 'workspace-1',
        directory: '/workspace',
        title: 'Invalid Session',
      };

      const error = new Error('Validation error');
      mockApi.post.mockRejectedValueOnce(error);

      await expect(sessionsApi.create(createData)).rejects.toThrow('Validation error');
    });
  });

  describe('getByExternalId', () => {
    it('should call api.get with correct URL for external session id', async () => {
      const mockSession: Session = {
        id: 1,
        session_unique_id: 'session-123',
        external_session_id: 'ext-session-123',
        project_unique_id: 'project-1',
        workspace_unique_id: 'workspace-1',
        directory: '/workspace',
        title: 'Test Session',
        gmt_create: 1234567890,
        gmt_modified: 1234567890,
        time_compacting: null,
        time_archived: null,
      };

      mockApi.get.mockResolvedValueOnce(mockSession);

      const result = await sessionsApi.getByExternalId('ext-session-123');

      expect(mockApi.get).toHaveBeenCalledWith('/sessions/?external_session_id=ext-session-123');
      expect(result).toEqual(mockSession);
      expect(result.external_session_id).toBe('ext-session-123');
    });

    it('should handle not found error for external session id', async () => {
      const error = new Error('Session not found');
      mockApi.get.mockRejectedValueOnce(error);

      await expect(sessionsApi.getByExternalId('nonexistent-ext-id')).rejects.toThrow('Session not found');
    });
  });
});
