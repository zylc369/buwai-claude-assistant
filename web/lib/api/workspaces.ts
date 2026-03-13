import { api } from './client';
import { Workspace, CreateWorkspaceRequest, UpdateWorkspaceRequest } from './types';

export const workspacesApi = {
  list: (projectUniqueId: string) =>
    api.get<Workspace[]>(`/workspaces/?project_unique_id=${projectUniqueId}`),

  get: (workspaceUniqueId: string) =>
    api.get<Workspace>(`/workspaces/${workspaceUniqueId}`),

  create: (data: CreateWorkspaceRequest) =>
    api.post<Workspace>('/workspaces/', data),

  update: (workspaceUniqueId: string, data: UpdateWorkspaceRequest) =>
    api.put<Workspace>(`/workspaces/${workspaceUniqueId}`, data),

  delete: (workspaceUniqueId: string) =>
    api.delete<void>(`/workspaces/${workspaceUniqueId}`),
};
