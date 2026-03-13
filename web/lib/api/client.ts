import type {
  Project,
  CreateProjectRequest,
  UpdateProjectRequest,
  ListProjectsParams,
  Workspace,
  CreateWorkspaceRequest,
  UpdateWorkspaceRequest,
  ListWorkspacesParams,
  Session,
  CreateSessionRequest,
  UpdateSessionRequest,
  ListSessionsParams,
  Message,
  CreateMessageRequest,
  ListMessagesParams,
  AISendRequest,
  SSEEvent,
  SSEConnectionState,
  SSEState,
  SessionExecutionState,
  PersistedState,
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const STORAGE_KEYS = {
  SESSION_EXECUTION_STATE: 'buwai-session-execution-state',
  PERSISTED_IDS: 'buwai-persisted-ids',
} as const;

export interface ApiError {
  detail: string;
}

export class ApiClientError extends Error {
  status: number;
  
  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiClientError';
    this.status = status;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new ApiClientError(error.detail || 'An error occurred', response.status);
  }
  
  if (response.status === 204) {
    return {} as T;
  }
  
  return response.json();
}

async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const config: RequestInit = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  };
  
  const response = await fetch(url, config);
  return handleResponse<T>(response);
}

const api = {
  get: <T>(endpoint: string) => 
    fetchApi<T>(endpoint, { method: 'GET' }),
  
  post: <T>(endpoint: string, data?: unknown) =>
    fetchApi<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    }),
  
  put: <T>(endpoint: string, data?: unknown) =>
    fetchApi<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    }),
  
  delete: <T>(endpoint: string) =>
    fetchApi<T>(endpoint, { method: 'DELETE' }),
};

function buildQueryString<T extends object>(params: T | undefined): string {
  if (!params) return '';
  
  const searchParams = new URLSearchParams();
  
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null) {
      searchParams.append(key, String(value));
    }
  }
  
  const queryString = searchParams.toString();
  return queryString ? `?${queryString}` : '';
}

export class APIClient {
  // ============================================
  // Project methods
  // ============================================
  
  async getProjects(params?: ListProjectsParams): Promise<Project[]> {
    const query = buildQueryString(params);
    return api.get<Project[]>(`/projects/${query}`);
  }
  
  async createProject(data: CreateProjectRequest): Promise<Project> {
    return api.post<Project>('/projects/', data);
  }
  
  async getProjectByUniqueId(projectUniqueId: string): Promise<Project> {
    return api.get<Project>(`/projects/${projectUniqueId}`);
  }
  
  async updateProject(projectUniqueId: string, data: UpdateProjectRequest): Promise<Project> {
    return api.put<Project>(`/projects/${projectUniqueId}`, data);
  }
  
  async deleteProject(projectUniqueId: string): Promise<void> {
    return api.delete<void>(`/projects/${projectUniqueId}`);
  }
  
  // ============================================
  // Workspace methods
  // ============================================
  
  async getWorkspaces(params: ListWorkspacesParams): Promise<Workspace[]> {
    const query = buildQueryString(params);
    return api.get<Workspace[]>(`/workspaces/${query}`);
  }
  
  async createWorkspace(data: CreateWorkspaceRequest): Promise<Workspace> {
    return api.post<Workspace>('/workspaces/', data);
  }
  
  async getWorkspaceByUniqueId(workspaceUniqueId: string): Promise<Workspace> {
    return api.get<Workspace>(`/workspaces/${workspaceUniqueId}`);
  }
  
  async updateWorkspace(workspaceUniqueId: string, data: UpdateWorkspaceRequest): Promise<Workspace> {
    return api.put<Workspace>(`/workspaces/${workspaceUniqueId}`, data);
  }
  
  async deleteWorkspace(workspaceUniqueId: string): Promise<void> {
    return api.delete<void>(`/workspaces/${workspaceUniqueId}`);
  }
  
  // ============================================
  // Session methods
  // ============================================
  
  async getSessions(params: ListSessionsParams): Promise<Session[]> {
    const query = buildQueryString(params);
    return api.get<Session[]>(`/sessions/${query}`);
  }
  
  async createSession(data: CreateSessionRequest): Promise<Session> {
    return api.post<Session>('/sessions/', data);
  }
  
  async getSessionByUniqueId(sessionUniqueId: string): Promise<Session> {
    return api.get<Session>(`/sessions/${sessionUniqueId}`);
  }
  
  async updateSession(sessionUniqueId: string, data: UpdateSessionRequest): Promise<Session> {
    return api.put<Session>(`/sessions/${sessionUniqueId}`, data);
  }
  
  async deleteSession(sessionUniqueId: string): Promise<void> {
    return api.delete<void>(`/sessions/${sessionUniqueId}`);
  }
  
  async archiveSession(sessionUniqueId: string): Promise<Session> {
    return api.post<Session>(`/sessions/${sessionUniqueId}/archive`);
  }
  
  async unarchiveSession(sessionUniqueId: string): Promise<Session> {
    return api.post<Session>(`/sessions/${sessionUniqueId}/unarchive`);
  }
  
  // ============================================
  // Message methods
  // ============================================
  
  async getMessages(params: ListMessagesParams): Promise<Message[]> {
    const query = buildQueryString(params);
    return api.get<Message[]>(`/messages/${query}`);
  }
  
  async createMessage(data: CreateMessageRequest): Promise<Message> {
    return api.post<Message>('/messages/', data);
  }
  
  async getMessageByUniqueId(messageUniqueId: string): Promise<Message> {
    return api.get<Message>(`/messages/${messageUniqueId}`);
  }
  
  // ============================================
  // AI Send method (streaming)
  // ============================================
  
  async sendAIPrompt(request: AISendRequest, signal?: AbortSignal): Promise<Response> {
    const url = `${API_BASE_URL}/messages/send`;
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
      signal,
    });
    
    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new ApiClientError(error.detail || 'An error occurred', response.status);
    }
    
    return response;
  }
  
  async *streamAIResponse(request: AISendRequest, signal?: AbortSignal): AsyncGenerator<SSEEvent> {
    const response = await this.sendAIPrompt(request, signal);
    const reader = response.body?.getReader();
    
    if (!reader) {
      throw new ApiClientError('No response body', 500);
    }
    
    const decoder = new TextDecoder();
    let buffer = '';
    
    while (true) {
      const { done, value } = await reader.read();
      
      if (done) {
        break;
      }
      
      buffer += decoder.decode(value, { stream: true });
      
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data.trim()) {
            try {
              const event = JSON.parse(data) as SSEEvent;
              yield event;
            } catch {
              // Skip malformed JSON
            }
          }
        }
      }
    }
  }

  // ============================================
  // SSE Connection methods
  // ============================================

  connectSSE(endpoint: string, onMessage: (event: SSEEvent) => void, onError?: (error: Error) => void): () => void {
    const url = `${API_BASE_URL}${endpoint}`;
    const eventSource = new EventSource(url);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as SSEEvent;
        onMessage(data);
      } catch {
        // Skip malformed JSON
      }
    };

    eventSource.onerror = () => {
      const error = new Error('SSE connection error');
      onError?.(error);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }

  createSSEConnection(
    endpoint: string,
    handlers: {
      onMessage?: (event: SSEEvent) => void;
      onError?: (error: Error) => void;
      onOpen?: () => void;
    }
  ): () => void {
    const url = `${API_BASE_URL}${endpoint}`;
    const eventSource = new EventSource(url);

    eventSource.onopen = () => {
      handlers.onOpen?.();
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as SSEEvent;
        handlers.onMessage?.(data);
      } catch {
        // Skip malformed JSON
      }
    };

    eventSource.onerror = () => {
      const error = new Error('SSE connection error');
      handlers.onError?.(error);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }

  // ============================================
  // Session Execution State methods
  // ============================================

  getSessionState(sessionUniqueId: string): SessionExecutionState | null {
    if (typeof window === 'undefined') return null;
    
    const stored = localStorage.getItem(STORAGE_KEYS.SESSION_EXECUTION_STATE);
    if (!stored) return null;
    
    try {
      const states = JSON.parse(stored) as Record<string, SessionExecutionState>;
      return states[sessionUniqueId] || null;
    } catch {
      return null;
    }
  }

  saveSessionState(state: SessionExecutionState): void {
    if (typeof window === 'undefined') return;
    
    const stored = localStorage.getItem(STORAGE_KEYS.SESSION_EXECUTION_STATE);
    let states: Record<string, SessionExecutionState> = {};
    
    try {
      states = stored ? JSON.parse(stored) : {};
    } catch {
      states = {};
    }
    
    states[state.session_unique_id] = state;
    localStorage.setItem(STORAGE_KEYS.SESSION_EXECUTION_STATE, JSON.stringify(states));
  }

  loadSessionState(): Record<string, SessionExecutionState> {
    if (typeof window === 'undefined') return {};
    
    const stored = localStorage.getItem(STORAGE_KEYS.SESSION_EXECUTION_STATE);
    if (!stored) return {};
    
    try {
      return JSON.parse(stored) as Record<string, SessionExecutionState>;
    } catch {
      return {};
    }
  }

  clearSessionState(sessionUniqueId: string): void {
    if (typeof window === 'undefined') return;
    
    const stored = localStorage.getItem(STORAGE_KEYS.SESSION_EXECUTION_STATE);
    if (!stored) return;
    
    try {
      const states = JSON.parse(stored) as Record<string, SessionExecutionState>;
      delete states[sessionUniqueId];
      localStorage.setItem(STORAGE_KEYS.SESSION_EXECUTION_STATE, JSON.stringify(states));
    } catch {
      // Ignore parsing errors
    }
  }

  // ============================================
  // Persistence methods (project/workspace/session IDs)
  // ============================================

  savePersistedIds(state: PersistedState): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem(STORAGE_KEYS.PERSISTED_IDS, JSON.stringify(state));
  }

  loadPersistedIds(): PersistedState {
    if (typeof window === 'undefined') return {};
    
    const stored = localStorage.getItem(STORAGE_KEYS.PERSISTED_IDS);
    if (!stored) return {};
    
    try {
      return JSON.parse(stored) as PersistedState;
    } catch {
      return {};
    }
  }

  clearPersistedIds(): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(STORAGE_KEYS.PERSISTED_IDS);
  }
}

export const apiClient = new APIClient();
export { api };
