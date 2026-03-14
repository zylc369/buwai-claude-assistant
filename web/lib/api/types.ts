/**
 * API Types - TypeScript interfaces for API requests and responses
 */

// ============================================
// Project types
// ============================================

export interface Project {
  id: number;
  project_unique_id: string;
  directory: string;
  branch: string | null;
  name: string;
  gmt_create: number;
  gmt_modified: number;
  latest_active_time: number | null;
}

export interface CreateProjectRequest {
  project_unique_id: string;
  directory: string;
  name: string;
  branch?: string | null;
}

export interface UpdateProjectRequest {
  directory?: string;
  name?: string;
  branch?: string | null;
}

export interface ListProjectsParams {
  offset?: number;
  limit?: number;
  name?: string;
}

// ============================================
// Workspace types
// ============================================

export interface Workspace {
  id: number;
  workspace_unique_id: string;
  project_unique_id: string;
  branch: string | null;
  directory: string;
  extra: string | null;
  gmt_create: number;
  gmt_modified: number;
  latest_active_time: number | null;
}

export interface CreateWorkspaceRequest {
  workspace_unique_id: string;
  project_unique_id: string;
  branch?: string | null;
  directory: string;
  extra?: string | null;
}

export interface UpdateWorkspaceRequest {
  branch?: string | null;
  directory?: string;
  extra?: string | null;
}

export interface ListWorkspacesParams {
  project_unique_id: string;
  offset?: number;
  limit?: number;
}

// ============================================
// Session types (Conversation)
// ============================================

export interface Session {
  id: number;
  session_unique_id: string;
  external_session_id: string;
  sdk_session_id?: string | null;
  project_unique_id: string;
  workspace_unique_id: string;
  directory: string;
  title: string;
  gmt_create: number;
  gmt_modified: number;
  time_compacting: number | null;
  time_archived: number | null;
}

export interface CreateSessionRequest {
  session_unique_id: string;
  external_session_id: string;
  project_unique_id: string;
  workspace_unique_id: string;
  directory: string;
  title: string;
}

export interface UpdateSessionRequest {
  title?: string;
  directory?: string;
  time_compacting?: number | null;
}

export interface ListSessionsParams {
  project_unique_id: string;
  workspace_unique_id: string;
  offset?: number;
  limit?: number;
  include_archived?: boolean;
}

// ============================================
// Message types
// ============================================

export interface Message {
  id: number;
  message_unique_id: string;
  session_unique_id: string;
  gmt_create: number;
  gmt_modified: number;
  data: string;
}

export interface CreateMessageRequest {
  message_unique_id: string;
  session_unique_id: string;
  data: Record<string, unknown>;
}

export interface UpdateMessageRequest {
  data?: Record<string, unknown>;
}

export interface ListMessagesParams {
  session_unique_id: string;
  offset?: number;
  limit?: number;
  last_message_id?: number;
}

// ============================================
// AI Send types
// ============================================

export interface AISendRequest {
  prompt: string;
  session_unique_id: string;
  cwd: string;
  settings: string;
  system_prompt?: string;
}

export interface AISendResponse {
  session_unique_id: string;
  status: string;
}

export interface SSEEvent {
  type: 'chunk' | 'done' | 'error';
  content?: unknown;
  session_unique_id?: string;
  message?: string;
  sdk_session_id?: string;
}

// ============================================
// SSE Connection State types
// ============================================

export type SSEConnectionState = 
  | 'connecting'
  | 'connected'
  | 'receiving'
  | 'idle'
  | 'disconnected'
  | 'error';

export interface SSEState {
  connectionState: SSEConnectionState;
  lastError?: string;
  reconnectAttempts: number;
}

// ============================================
// Session Execution State types
// ============================================

export type SessionExecutionStatus = 'idle' | 'executing';

export interface SessionExecutionState {
  session_unique_id: string;
  status: SessionExecutionStatus;
  lastMessage?: string;
  lastMessageTime?: number;
}

// ============================================
// LocalStorage Persistence types
// ============================================

export interface PersistedState {
  project_unique_id?: string;
  workspace_unique_id?: string;
  session_unique_id?: string;
}

// ============================================
// Legacy types (for backward compatibility)
// ============================================

export interface User {
  id: number;
  email: string;
  username: string;
  full_name: string | null;
  is_active: boolean;
  is_admin: boolean;
}

export interface CreateUserRequest {
  email: string;
  username: string;
  password: string;
  full_name?: string;
}

export interface UpdateUserRequest {
  email?: string;
  username?: string;
  full_name?: string;
  is_active?: boolean;
}

export interface Task {
  id: number;
  title: string;
  description: string | null;
  project_id: number;
  assignee_id: number | null;
  status: TaskStatus;
  priority: TaskPriority;
  due_date: string | null;
}

export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'cancelled';
export type TaskPriority = 'low' | 'normal' | 'high';

export interface CreateTaskRequest {
  title: string;
  project_id: number;
  description?: string;
  assignee_id?: number;
  status?: TaskStatus;
  priority?: TaskPriority;
  due_date?: string;
}

export interface UpdateTaskRequest {
  title?: string;
  description?: string;
  assignee_id?: number;
  status?: TaskStatus;
  priority?: TaskPriority;
  due_date?: string;
}

export type ChatSession = Session;
