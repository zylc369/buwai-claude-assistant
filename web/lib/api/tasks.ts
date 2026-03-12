/**
 * Tasks API client
 */

import { api } from './client';
import { Task, CreateTaskRequest, UpdateTaskRequest } from './types';

export const tasksApi = {
  list: (params?: { project_id?: number; assignee_id?: number; status?: string }) =>
    api.get<Task[]>('/tasks/', { params }),
  
  get: (id: number) => api.get<Task>(`/tasks/${id}`),
  
  create: (data: CreateTaskRequest) =>
    api.post<Task>('/tasks/', data),
  
  update: (id: number, data: UpdateTaskRequest) =>
    api.put<Task>(`/tasks/${id}`, data),
  
  delete: (id: number) => api.delete<void>(`/tasks/${id}`),
  
  getOverdue: () => api.get<Task[]>('/tasks/overdue/'),
};
