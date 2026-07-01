/**
 * chatService.ts
 *
 * Thin service layer — keeps React components decoupled from api.ts.
 */

import api from "@/lib/api"
import type { ChatResponse, ConversationDetailResponse, ConversationsListResponse } from "@/lib/api"

export type { ChatResponse, ConversationDetailResponse, ConversationsListResponse }

const chatService = {
  chat: (message: string, conversationId?: string | null) =>
    api.sendMessage(message, conversationId),

  getConversations: () => api.getConversations(),

  getConversation: (id: string) => api.getConversation(id),

  deleteConversation: (id: string) => api.deleteConversation(id),
}

export default chatService
