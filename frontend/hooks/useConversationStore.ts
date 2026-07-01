/**
 * hooks/useConversationStore.ts
 *
 * React hook for accessing and managing conversations.
 *
 * Features:
 * - Automatic initialization
 * - Reactive updates (re-render on changes)
 * - Simplified API for components
 * - No direct store access needed
 *
 * Usage:
 * const { conversations, activeConversation, createConversation, updateConversation } = useConversationStore(activeId)
 */

import { useEffect, useState, useCallback } from "react"
import {
  initializeStore,
  createConversation as storeCreate,
  getConversation as storeGet,
  getAllConversations,
  updateConversation as storeUpdate,
  deleteConversation as storeDelete,
} from "@/store/conversationStore"
import type { Conversation } from "@/types/conversation"
import { formatRelativeTime } from "@/types/conversation"
import type { Message, TripSummary } from "@/lib/travel"

/**
 * Hook for managing conversations in a React component.
 *
 * @param activeId - Current active conversation ID (optional)
 * @returns Object with conversations and methods
 */
export function useConversationStore(activeId?: string) {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [isLoaded, setIsLoaded] = useState(false)

  // Initialize store on mount
  useEffect(() => {
    initializeStore()
    refreshConversations()
    setIsLoaded(true)
  }, [])

  /**
   * Refresh conversations from store.
   * Also updates the UI list format for sidebar display.
   */
  const refreshConversations = useCallback(() => {
    const all = getAllConversations()
    setConversations(all)
  }, [])

  /**
   * Create a new conversation.
   *
   * @returns The created conversation
   */
  const createConversation = useCallback(() => {
    const conversation = storeCreate()
    refreshConversations()
    return conversation
  }, [refreshConversations])

  /**
   * Get the currently active conversation.
   *
   * @returns The active conversation or undefined
   */
  const getActiveConversation = useCallback((): Conversation | undefined => {
    if (!activeId) return undefined
    return storeGet(activeId)
  }, [activeId])

  /**
   * Update the active conversation with new messages.
   *
   * @param messages - New messages array
   */
  const updateMessages = useCallback(
    (messages: Message[]) => {
      if (!activeId) return
      storeUpdate(activeId, { messages })
      refreshConversations()
    },
    [activeId, refreshConversations],
  )

  /**
   * Update the active conversation with new trip data.
   *
   * @param trip - New trip summary
   */
  const updateTrip = useCallback(
    (trip: TripSummary) => {
      if (!activeId) return
      storeUpdate(activeId, { trip })
      refreshConversations()
    },
    [activeId, refreshConversations],
  )

  /**
   * Delete a conversation.
   *
   * @param id - Conversation ID to delete
   */
  const deleteConversation = useCallback(
    (id: string) => {
      storeDelete(id)
      refreshConversations()
    },
    [refreshConversations],
  )

  /**
   * Get conversations formatted for sidebar display.
   * Includes title, preview, and formatted time.
   *
   * @returns Formatted conversations for UI
   */
  const getFormattedConversations = useCallback(() => {
    return conversations.map((c) => ({
      ...c,
      preview: c.messages.length > 0 ? c.messages[0].content.substring(0, 50) : "No messages yet",
      displayTime: formatRelativeTime(c.updatedAt),
    }))
  }, [conversations])

  return {
    // State
    conversations,
    isLoaded,

    // Getters
    activeConversation: getActiveConversation(),
    formattedConversations: getFormattedConversations(),

    // Actions
    createConversation,
    updateMessages,
    updateTrip,
    deleteConversation,
    refresh: refreshConversations,
  }
}
