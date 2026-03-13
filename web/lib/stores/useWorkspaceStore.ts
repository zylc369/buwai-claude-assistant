import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Workspace } from '@/lib/api/types';

interface WorkspaceState {
  selectedWorkspace: Workspace | null;
  setSelectedWorkspace: (workspace: Workspace | null) => void;
  clearWorkspace: () => void;
}

export const useWorkspaceStore = create<WorkspaceState>()(
  persist(
    (set) => ({
      selectedWorkspace: null,
      setSelectedWorkspace: (workspace) => set({ selectedWorkspace: workspace }),
      clearWorkspace: () => set({ selectedWorkspace: null }),
    }),
    {
      name: 'buwai-workspace-storage',
    }
  )
);
