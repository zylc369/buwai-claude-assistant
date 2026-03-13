'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { sessionsApi } from '@/lib/api/sessions';
import { Session, CreateSessionRequest, ListSessionsParams } from '@/lib/api/types';

export function useSessions(params: ListSessionsParams) {
  return useQuery<Session[]>({
    queryKey: ['sessions', params],
    queryFn: () => sessionsApi.list(params),
  });
}

export function useSession(sessionUniqueId: string) {
  return useQuery<Session>({
    queryKey: ['sessions', sessionUniqueId],
    queryFn: () => sessionsApi.get(sessionUniqueId),
    enabled: !!sessionUniqueId,
  });
}

export function useSessionByExternalId(externalSessionId: string) {
  return useQuery<Session>({
    queryKey: ['sessions', 'external', externalSessionId],
    queryFn: () => sessionsApi.getByExternalId(externalSessionId),
    enabled: !!externalSessionId,
  });
}

export function useCreateSession() {
  const queryClient = useQueryClient();
  
  return useMutation<Session, Error, CreateSessionRequest>({
    mutationFn: sessionsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
    },
  });
}
