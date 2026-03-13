/**
 * Tasks API client
 */

import { api } from './client';
import { Task, CreateTaskRequest, UpdateTaskRequest } from './types';

export const tasksApi = {
  list: (params?: { project_id?: number; assignee_id?: number; status?: string }) => {
    const queryParams = new URLSearchParams();
    if (params?.project_id) queryParams.append('project_id', params.project_id.toString());
    if (params?.assignee_id) queryParams.append('assignee_id', params.assignee_id.toString());
    if (params?.status) queryParams.append('status', params.status);
    const url = queryParams.toString() ? `/tasks/?${queryParams.toString()}` : '/tasks/';
    return api.get<Task[]>(url);
  },
  
  get: (id: number) => api.get<Task>(`/tasks/${id}`),
  
  create: (data: CreateTaskRequest) =>
    api.post<Task>('/tasks/', data),
  
  update: (id: number, data: UpdateTaskRequest) =>
    api.put<Task>(`/tasks/${id}`, data),
  
  delete: (id: number) => api.delete<void>(`/tasks/${id}`),
  
  getOverdue: () => api.get<Task[]>('/tasks/overdue/'),
};
