/**
 * React Query hooks for tasks
 */

'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { tasksApi } from '@/lib/api/tasks';
import { Task, CreateTaskRequest, UpdateTaskRequest } from '@/lib/api/types';

interface TaskFilters {
  projectId?: number;
  assigneeId?: number;
  status?: string;
}

export function useTasks(filters?: TaskFilters) {
  return useQuery<Task[]>({
    queryKey: ['tasks', filters],
    queryFn: () => tasksApi.list(filters),
  });
}

export function useTask(id: number) {
  return useQuery<Task>({
    queryKey: ['tasks', id],
    queryFn: () => tasksApi.get(id),
    enabled: !!id,
  });
}

export function useOverdueTasks() {
  return useQuery<Task[]>({
    queryKey: ['tasks', 'overdue'],
    queryFn: tasksApi.getOverdue,
  });
}

export function useCreateTask() {
  const queryClient = useQueryClient();
  
  return useMutation<Task, Error, CreateTaskRequest>({
    mutationFn: tasksApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
}

export function useUpdateTask() {
  const queryClient = useQueryClient();
  
  return useMutation<Task, Error, { id: number; data: UpdateTaskRequest }>({
    mutationFn: ({ id, data }) => tasksApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
}

export function useDeleteTask() {
  const queryClient = useQueryClient();
  
  return useMutation<void, Error, number>({
    mutationFn: tasksApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
}
