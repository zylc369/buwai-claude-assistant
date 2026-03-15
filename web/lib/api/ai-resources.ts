import { api } from './client';
import {
  AIResource,
  CreateAIResourceRequest,
  UpdateAIResourceRequest,
  ListAIResourcesParams,
} from './types';

const buildQuery = (params?: ListAIResourcesParams): string => {
  if (!params) return '';

  const searchParams = new URLSearchParams();

  if (params.offset !== undefined) searchParams.set('offset', String(params.offset));
  if (params.limit !== undefined) searchParams.set('limit', String(params.limit));
  if (params.type) searchParams.set('type', params.type);
  if (params.owner) searchParams.set('owner', params.owner);
  if (params.test !== undefined) searchParams.set('test', String(params.test));
  if (params.disabled !== undefined) searchParams.set('disabled', String(params.disabled));

  const query = searchParams.toString();
  return query ? `?${query}` : '';
};

export const aiResourcesApi = {
  list: (params?: ListAIResourcesParams) =>
    api.get<AIResource[]>(`/ai-resources/${buildQuery(params)}`),

  get: (resourceUniqueId: string) =>
    api.get<AIResource>(`/ai-resources/${resourceUniqueId}`),

  create: (data: CreateAIResourceRequest) =>
    api.post<AIResource>('/ai-resources/', data),

  update: (resourceUniqueId: string, data: UpdateAIResourceRequest) =>
    api.put<AIResource>(`/ai-resources/${resourceUniqueId}`, data),

  delete: (resourceUniqueId: string) =>
    api.delete<void>(`/ai-resources/${resourceUniqueId}`),
};
