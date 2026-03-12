/**
 * API Types - TypeScript interfaces for API responses
 */

// User types
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

// Project types
export interface Project {
  id: number;
  name: string;
  description: string | null;
  owner_id: number;
}

export interface CreateProjectRequest {
  name: string;
  owner_id: number;
  description?: string;
}

export interface UpdateProjectRequest {
  name?: string;
  description?: string;
}

// Task types
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

// Session types
export interface Session {
  id: number;
  user_id: number;
  token: string;
  expires_at: string;
}

export interface CreateSessionRequest {
  user_id: number;
  expires_in_hours?: number;
}
