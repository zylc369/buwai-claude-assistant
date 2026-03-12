/**
 * Project store - Zustand state management
 */

import { create } from 'zustand';
import { Project } from '@/lib/api/types';

interface ProjectState {
  projects: Project[];
  selectedProject: Project | null;
  loading: boolean;
  error: string | null;
  
  setProjects: (projects: Project[]) => void;
  setSelectedProject: (project: Project | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  addProject: (project: Project) => void;
  updateProject: (id: number, project: Partial<Project>) => void;
  removeProject: (id: number) => void;
}

export const useProjectStore = create<ProjectState>((set) => ({
  projects: [],
  selectedProject: null,
  loading: false,
  error: null,
  
  setProjects: (projects) => set({ projects }),
  setSelectedProject: (project) => set({ selectedProject: project }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  
  addProject: (project) => set((state) => ({
    projects: [...state.projects, project]
  })),
  
  updateProject: (id, updatedProject) => set((state) => ({
    projects: state.projects.map((project) =>
      project.id === id ? { ...project, ...updatedProject } : project
    ),
    selectedProject: state.selectedProject?.id === id 
      ? { ...state.selectedProject, ...updatedProject } 
      : state.selectedProject
  })),
  
  removeProject: (id) => set((state) => ({
    projects: state.projects.filter((project) => project.id !== id),
    selectedProject: state.selectedProject?.id === id ? null : state.selectedProject
  })),
}));
