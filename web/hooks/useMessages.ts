/**
 * React Query hooks for messages
 */

'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { 
  Message, 
  CreateMessageRequest, 
  ListMessagesParams 
} from '@/lib/api/types';

export function useMessages(params: ListMessagesParams) {
  return useQuery<Message[]>({
    queryKey: ['messages', params.session_unique_id, params.offset, params.limit, params.last_message_id],
    queryFn: () => apiClient.getMessages(params),
    enabled: !!params.session_unique_id,
  });
}

export function useMessage(messageUniqueId: string) {
  return useQuery<Message>({
    queryKey: ['messages', messageUniqueId],
    queryFn: () => apiClient.getMessageByUniqueId(messageUniqueId),
    enabled: !!messageUniqueId,
  });
}

export function useCreateMessage() {
  const queryClient = useQueryClient();
  
  return useMutation<Message, Error, CreateMessageRequest>({
    mutationFn: (data) => apiClient.createMessage(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ 
        queryKey: ['messages', variables.session_unique_id] 
      });
    },
  });
}
