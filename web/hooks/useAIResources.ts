'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { aiResourcesApi } from '@/lib/api/ai-resources';
import {
  AIResource,
  CreateAIResourceRequest,
  UpdateAIResourceRequest,
  ListAIResourcesParams,
} from '@/lib/api/types';

export function useAIResources(params?: ListAIResourcesParams) {
  return useQuery<AIResource[]>({
    queryKey: ['ai-resources', params],
    queryFn: () => aiResourcesApi.list(params),
  });
}

export function useAIResource(resourceUniqueId: string | undefined) {
  return useQuery<AIResource>({
    queryKey: ['ai-resources', resourceUniqueId],
    queryFn: () => aiResourcesApi.get(resourceUniqueId!),
    enabled: !!resourceUniqueId,
  });
}

export function useCreateAIResource() {
  const queryClient = useQueryClient();

  return useMutation<AIResource, Error, CreateAIResourceRequest>({
    mutationFn: aiResourcesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-resources'] });
    },
  });
}

export function useUpdateAIResource() {
  const queryClient = useQueryClient();

  return useMutation<
    AIResource,
    Error,
    { resourceUniqueId: string; data: UpdateAIResourceRequest }
  >({
    mutationFn: ({ resourceUniqueId, data }) =>
      aiResourcesApi.update(resourceUniqueId, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['ai-resources'] });
      queryClient.invalidateQueries({
        queryKey: ['ai-resources', data.resource_unique_id],
      });
    },
  });
}

export function useDeleteAIResource() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, { resourceUniqueId: string }>({
    mutationFn: ({ resourceUniqueId }) => aiResourcesApi.delete(resourceUniqueId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-resources'] });
    },
  });
}
