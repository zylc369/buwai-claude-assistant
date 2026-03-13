/**
 * Users API client
 */

import { api } from './client';
import { User, CreateUserRequest, UpdateUserRequest } from './types';

export const usersApi = {
  list: () => api.get<User[]>('/users/'),
  
  get: (id: number) => api.get<User>(`/users/${id}`),
  
  create: (data: CreateUserRequest) => 
    api.post<User>('/users/', data),
  
  update: (id: number, data: UpdateUserRequest) => 
    api.put<User>(`/users/${id}`, data),
  
  delete: (id: number) => 
    api.delete<void>(`/users/${id}`),
};
