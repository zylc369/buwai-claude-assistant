'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { workspacesApi } from '@/lib/api/workspaces';
import { Workspace, CreateWorkspaceRequest, UpdateWorkspaceRequest } from '@/lib/api/types';

export function useWorkspaces(projectUniqueId: string | undefined) {
  return useQuery<Workspace[]>({
    queryKey: ['workspaces', projectUniqueId],
    queryFn: () => {
      if (!projectUniqueId) return Promise.resolve([]);
      return workspacesApi.list(projectUniqueId);
    },
    enabled: !!projectUniqueId,
  });
}

export function useWorkspace(workspaceUniqueId: string) {
  return useQuery<Workspace>({
    queryKey: ['workspaces', workspaceUniqueId],
    queryFn: () => workspacesApi.get(workspaceUniqueId),
    enabled: !!workspaceUniqueId,
  });
}

export function useCreateWorkspace() {
  const queryClient = useQueryClient();

  return useMutation<Workspace, Error, CreateWorkspaceRequest>({
    mutationFn: workspacesApi.create,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['workspaces', data.project_unique_id] });
    },
  });
}

export function useUpdateWorkspace() {
  const queryClient = useQueryClient();

  return useMutation<Workspace, Error, { workspaceUniqueId: string; data: UpdateWorkspaceRequest }>({
    mutationFn: ({ workspaceUniqueId, data }) => workspacesApi.update(workspaceUniqueId, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['workspaces', data.project_unique_id] });
    },
  });
}

export function useDeleteWorkspace() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, { workspaceUniqueId: string; projectUniqueId: string }>({
    mutationFn: ({ workspaceUniqueId }) => workspacesApi.delete(workspaceUniqueId),
    onSuccess: (_, { projectUniqueId }) => {
      queryClient.invalidateQueries({ queryKey: ['workspaces', projectUniqueId] });
    },
  });
}
