import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import {
  useSessions,
  useSession,
  useSessionByExternalId,
  useCreateSession,
} from '../hooks/useSessions';
import { sessionsApi } from '../lib/api/sessions';
import { Session, CreateSessionRequest, ListSessionsParams } from '../lib/api/types';

// Mock the sessionsApi
vi.mock('../lib/api/sessions', () => ({
  sessionsApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    getByExternalId: vi.fn(),
  },
}));

const mockSessionsApi = vi.mocked(sessionsApi);

// Helper to create wrapper with QueryClient
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

// Mock session data factory
function createMockSession(overrides?: Partial<Session>): Session {
  return {
    id: 1,
    session_unique_id: 'session-1',
    external_session_id: 'ext-session-1',
    sdk_session_id: null,
    project_unique_id: 'project-1',
    workspace_unique_id: 'workspace-1',
    directory: '/workspace',
    title: 'Test Session',
    gmt_create: 1234567890,
    gmt_modified: 1234567890,
    time_compacting: null,
    time_archived: null,
    ...overrides,
  };
}

describe('useSessions hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('useSessions', () => {
    it('should fetch sessions list successfully', async () => {
      const mockSessions = [
        createMockSession({ id: 1, session_unique_id: 'session-1' }),
        createMockSession({ id: 2, session_unique_id: 'session-2' }),
      ];

      mockSessionsApi.list.mockResolvedValueOnce(mockSessions);

      const params: ListSessionsParams = {
        project_unique_id: 'project-1',
        workspace_unique_id: 'workspace-1',
      };

      const { result } = renderHook(() => useSessions(params), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockSessionsApi.list).toHaveBeenCalledWith(params);
      expect(result.current.data).toEqual(mockSessions);
    });

    it('should handle error when fetching sessions fails', async () => {
      const error = new Error('Failed to fetch sessions');
      mockSessionsApi.list.mockRejectedValueOnce(error);

      const params: ListSessionsParams = {
        project_unique_id: 'project-1',
        workspace_unique_id: 'workspace-1',
      };

      const { result } = renderHook(() => useSessions(params), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toBeInstanceOf(Error);
    });

    it('should pass query params correctly', async () => {
      mockSessionsApi.list.mockResolvedValueOnce([]);

      const params: ListSessionsParams = {
        project_unique_id: 'project-1',
        workspace_unique_id: 'workspace-1',
        offset: 10,
        limit: 5,
        include_archived: true,
      };

      const { result } = renderHook(() => useSessions(params), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockSessionsApi.list).toHaveBeenCalledWith(params);
    });
  });

  describe('useSession', () => {
    it('should fetch single session by unique id', async () => {
      const mockSession = createMockSession({ session_unique_id: 'session-123' });

      mockSessionsApi.get.mockResolvedValueOnce(mockSession);

      const { result } = renderHook(() => useSession('session-123'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockSessionsApi.get).toHaveBeenCalledWith('session-123');
      expect(result.current.data).toEqual(mockSession);
    });

    it('should not fetch when sessionUniqueId is empty', async () => {
      const { result } = renderHook(() => useSession(''), {
        wrapper: createWrapper(),
      });

      // Query should be disabled
      expect(result.current.fetchStatus).toBe('idle');
      expect(mockSessionsApi.get).not.toHaveBeenCalled();
    });

    it('should handle error when session not found', async () => {
      const error = new Error('Session not found');
      mockSessionsApi.get.mockRejectedValueOnce(error);

      const { result } = renderHook(() => useSession('nonexistent'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toBeInstanceOf(Error);
    });
  });

  describe('useSessionByExternalId', () => {
    it('should fetch session by external session id', async () => {
      const mockSession = createMockSession({
        external_session_id: 'ext-session-456',
      });

      mockSessionsApi.getByExternalId.mockResolvedValueOnce(mockSession);

      const { result } = renderHook(
        () => useSessionByExternalId('ext-session-456'),
        { wrapper: createWrapper() }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockSessionsApi.getByExternalId).toHaveBeenCalledWith('ext-session-456');
      expect(result.current.data).toEqual(mockSession);
      expect(result.current.data?.external_session_id).toBe('ext-session-456');
    });

    it('should not fetch when externalSessionId is empty', async () => {
      const { result } = renderHook(() => useSessionByExternalId(''), {
        wrapper: createWrapper(),
      });

      // Query should be disabled
      expect(result.current.fetchStatus).toBe('idle');
      expect(mockSessionsApi.getByExternalId).not.toHaveBeenCalled();
    });

    it('should handle error when session by external id not found', async () => {
      const error = new Error('Session not found');
      mockSessionsApi.getByExternalId.mockRejectedValueOnce(error);

      const { result } = renderHook(
        () => useSessionByExternalId('nonexistent-ext-id'),
        { wrapper: createWrapper() }
      );

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toBeInstanceOf(Error);
    });
  });

  describe('useCreateSession', () => {
    it('should create session successfully', async () => {
      const createData: CreateSessionRequest = {
        session_unique_id: 'new-session',
        external_session_id: 'ext-new-session',
        project_unique_id: 'project-1',
        workspace_unique_id: 'workspace-1',
        directory: '/workspace',
        title: 'New Session',
      };

      const mockCreatedSession = createMockSession({
        id: 2,
        ...createData,
      });

      mockSessionsApi.create.mockResolvedValueOnce(mockCreatedSession);

      const { result } = renderHook(() => useCreateSession(), {
        wrapper: createWrapper(),
      });

      result.current.mutate(createData);

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockSessionsApi.create).toHaveBeenCalledWith(createData, expect.any(Object));
      expect(result.current.data).toEqual(mockCreatedSession);
    });

    it('should invalidate sessions query on success', async () => {
      const queryClient = new QueryClient({
        defaultOptions: {
          queries: {
            retry: false,
          },
        },
      });

      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      const mockCreatedSession = createMockSession();
      mockSessionsApi.create.mockResolvedValueOnce(mockCreatedSession);

      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      );

      const { result } = renderHook(() => useCreateSession(), { wrapper });

      const createData: CreateSessionRequest = {
        session_unique_id: 'new-session',
        external_session_id: 'ext-new-session',
        project_unique_id: 'project-1',
        workspace_unique_id: 'workspace-1',
        directory: '/workspace',
        title: 'New Session',
      };

      result.current.mutate(createData);

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['sessions'] });
    });

    it('should handle create session error', async () => {
      const error = new Error('Failed to create session');
      mockSessionsApi.create.mockRejectedValueOnce(error);

      const { result } = renderHook(() => useCreateSession(), {
        wrapper: createWrapper(),
      });

      const createData: CreateSessionRequest = {
        session_unique_id: 'new-session',
        external_session_id: 'ext-new-session',
        project_unique_id: 'project-1',
        workspace_unique_id: 'workspace-1',
        directory: '/workspace',
        title: 'New Session',
      };

      result.current.mutate(createData);

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toBeInstanceOf(Error);
    });
  });
});
