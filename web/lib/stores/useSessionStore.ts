import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { ChatSession, Project, Workspace } from '@/lib/api/types';
import { uuidv7 } from 'uuidv7';

interface SessionState {
  selectedSession: ChatSession | null;
  isNewSession: boolean;
  setSelectedSession: (session: ChatSession | null) => void;
  createNewSession: (project: Project, workspace: Workspace) => ChatSession;
  markSessionPersisted: (sessionUniqueId: string, title: string) => void;
  clearSession: () => void;
}

export const useSessionStore = create<SessionState>()(
  persist(
    (set, get) => ({
      selectedSession: null,
      isNewSession: false,

      setSelectedSession: (session) =>
        set({
          selectedSession: session,
          isNewSession: session ? !session.session_unique_id : false,
        }),

      createNewSession: (project, workspace) => {
        const newSession: ChatSession = {
          id: 0,
          session_unique_id: '',
          external_session_id: uuidv7(),
          project_unique_id: project.project_unique_id,
          workspace_unique_id: workspace.workspace_unique_id,
          directory: workspace.directory,
          title: 'New Chat',
          gmt_create: Date.now(),
          gmt_modified: Date.now(),
          time_compacting: null,
          time_archived: null,
        };
        set({ selectedSession: newSession, isNewSession: true });
        return newSession;
      },

      markSessionPersisted: (sessionUniqueId, title) => {
        const { selectedSession } = get();
        if (selectedSession && !selectedSession.session_unique_id) {
          set({
            selectedSession: {
              ...selectedSession,
              session_unique_id: sessionUniqueId,
              title: title || selectedSession.title,
            },
            isNewSession: false,
          });
        }
      },

      clearSession: () => set({ selectedSession: null, isNewSession: false }),
    }),
    {
      name: 'buwai-session-storage',
    }
  )
);
