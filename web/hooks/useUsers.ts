/**
 * React Query hooks for users
 */

'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { usersApi } from '@/lib/api/users';
import { User, CreateUserRequest, UpdateUserRequest } from '@/lib/api/types';

export function useUsers() {
  return useQuery<User[]>({
    queryKey: ['users'],
    queryFn: usersApi.list,
  });
}

export function useUser(id: number) {
  return useQuery<User>({
    queryKey: ['users', id],
    queryFn: () => usersApi.get(id),
    enabled: !!id,
  });
}

export function useCreateUser() {
  const queryClient = useQueryClient();
  
  return useMutation<User, Error, CreateUserRequest>({
    mutationFn: usersApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
}

export function useUpdateUser() {
  const queryClient = useQueryClient();
  
  return useMutation<User, Error, { id: number; data: UpdateUserRequest }>({
    mutationFn: ({ id, data }) => usersApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
}

export function useDeleteUser() {
  const queryClient = useQueryClient();
  
  return useMutation<void, Error, number>({
    mutationFn: usersApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
}
