import { api } from './client';
import { Session, CreateSessionRequest, ListSessionsParams } from './types';

export const sessionsApi = {
  list: (params: ListSessionsParams) => {
    const searchParams = new URLSearchParams();
    if (params.project_unique_id) {
      searchParams.append('project_unique_id', params.project_unique_id);
    }
    if (params.workspace_unique_id) {
      searchParams.append('workspace_unique_id', params.workspace_unique_id);
    }
    if (params.offset !== undefined) {
      searchParams.append('offset', params.offset.toString());
    }
    if (params.limit !== undefined) {
      searchParams.append('limit', params.limit.toString());
    }
    if (params.include_archived !== undefined) {
      searchParams.append('include_archived', params.include_archived.toString());
    }
    const query = searchParams.toString();
    const url = query ? `/sessions/?${query}` : '/sessions/';
    return api.get<Session[]>(url);
  },

  get: (sessionUniqueId: string) =>
    api.get<Session>(`/sessions/${sessionUniqueId}`),

  create: (data: CreateSessionRequest) =>
    api.post<Session>('/sessions/', data),

  getByExternalId: (externalSessionId: string) =>
    api.get<Session>(`/sessions/?external_session_id=${externalSessionId}`),
};
