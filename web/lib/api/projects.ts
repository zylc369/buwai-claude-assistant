/**
 * Projects API client
 */

import { api } from './client';
import { Project, CreateProjectRequest, UpdateProjectRequest } from './types';

export const projectsApi = {
  list: (ownerId?: number) => api.get<Project[]>('/projects/', {
      params: ownerId ? { owner_id: ownerId } : undefined 
    }),
  
  get: (id: number) => api.get<Project>(`/projects/${id}`),
  
  create: (data: CreateProjectRequest) =>
    api.post<Project>('/projects/', data),
  
  update: (id: number, data: UpdateProjectRequest) =>
    api.put<Project>(`/projects/${id}`, data),
  
  delete: (id: number) => api.delete<void>(`/projects/${id}`),
};
