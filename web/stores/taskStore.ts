/**
 * Task store - Zustand state management
 */

import { create } from 'zustand';
import { Task } from '@/lib/api/types';

interface TaskState {
  tasks: Task[];
  loading: boolean;
  error: string | null;
  filter: {
    projectId?: number;
    assigneeId?: number;
    status?: string;
  };
  
  setTasks: (tasks: Task[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setFilter: (filter: Partial<TaskState['filter']>) => void;
  addTask: (task: Task) => void;
  updateTask: (id: number, task: Partial<Task>) => void;
  removeTask: (id: number) => void;
}

export const useTaskStore = create<TaskState>((set) => ({
  tasks: [],
  loading: false,
  error: null,
  filter: {},
  
  setTasks: (tasks) => set({ tasks }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  setFilter: (filter) => set((state) => ({ filter: { ...state.filter, ...filter } })),
  
  addTask: (task) => set((state) => ({
    tasks: [...state.tasks, task]
  })),
  
  updateTask: (id, updatedTask) => set((state) => ({
    tasks: state.tasks.map((task) =>
      task.id === id ? { ...task, ...updatedTask } : task
    )
  })),
  
  removeTask: (id) => set((state) => ({
    tasks: state.tasks.filter((task) => task.id !== id)
  })),
}));
