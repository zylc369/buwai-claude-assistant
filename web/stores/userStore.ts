/**
 * User store - Zustand state management
 */

import { create } from 'zustand';
import { User } from '@/lib/api/types';

interface UserState {
  currentUser: User | null;
  users: User[];
  loading: boolean;
  error: string | null;
  
  setCurrentUser: (user: User | null) => void;
  setUsers: (users: User[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  addUser: (user: User) => void;
  updateUser: (id: number, user: Partial<User>) => void;
  removeUser: (id: number) => void;
}

export const useUserStore = create<UserState>((set) => ({
  currentUser: null,
  users: [],
  loading: false,
  error: null,
  
  setCurrentUser: (user) => set({ currentUser: user }),
  setUsers: (users) => set({ users }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  
  addUser: (user) => set((state) => ({
    users: [...state.users, user]
  })),
  
  updateUser: (id, updatedUser) => set((state) => ({
    users: state.users.map((user) =>
      user.id === id ? { ...user, ...updatedUser } : user
    ),
    currentUser: state.currentUser?.id === id 
      ? { ...state.currentUser, ...updatedUser } 
      : state.currentUser
  })),
  
  removeUser: (id) => set((state) => ({
    users: state.users.filter((user) => user.id !== id),
    currentUser: state.currentUser?.id === id ? null : state.currentUser
  })),
}));
