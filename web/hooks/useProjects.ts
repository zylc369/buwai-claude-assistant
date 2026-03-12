/**
 * React Query hooks for projects
 */

'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi } from '@/lib/api/projects';
import { Project, CreateProjectRequest, UpdateProjectRequest } from '@/lib/api/types';

export function useProjects(ownerId?: number) {
  return useQuery<Project[]>({
    queryKey: ['projects', ownerId],
    queryFn: () => projectsApi.list(ownerId),
  });
}

export function useProject(id: number) {
  return useQuery<Project>({
    queryKey: ['projects', id],
    queryFn: () => projectsApi.get(id),
    enabled: !!id,
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  
  return useMutation<Project, Error, CreateProjectRequest>({
    mutationFn: projectsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
}

export function useUpdateProject() {
  const queryClient = useQueryClient();
  
  return useMutation<Project, Error, { id: number; data: UpdateProjectRequest }>({
    mutationFn: ({ id, data }) => projectsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
}

export function useDeleteProject() {
  const queryClient = useQueryClient();
  
  return useMutation<void, Error, number>({
    mutationFn: projectsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
}
