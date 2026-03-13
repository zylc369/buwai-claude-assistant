import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { ChatSession } from '@/lib/api/types';

interface SessionState {
  selectedSession: ChatSession | null;
  setSelectedSession: (session: ChatSession | null) => void;
  clearSession: () => void;
}

export const useSessionStore = create<SessionState>()(
  persist(
    (set) => ({
      selectedSession: null,
      setSelectedSession: (session) => set({ selectedSession: session }),
      clearSession: () => set({ selectedSession: null }),
    }),
    {
      name: 'buwai-session-storage',
    }
  )
);
