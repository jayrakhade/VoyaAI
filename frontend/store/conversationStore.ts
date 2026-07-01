/**
 * store/conversationStore.ts
 *
 * Conversation store with localStorage persistence.
 *
 * Responsibilities:
 * - CRUD operations (Create, Read, Update, Delete)
 * - localStorage persistence
 * - Conversation list management
 * - Auto-save on changes
 *
 * This is a pure TypeScript store (no React dependencies).
 * React components use the useConversationStore hook.
 */

import type { Conversation } from "@/types/conversation"
import { createEmptyConversation, generateConversationTitle } from "@/types/conversation"
import type { Message, TripSummary } from "@/lib/travel"

const STORAGE_KEY = "voyaai_conversations"

/**
 * In-memory store for conversations.
 * Automatically synced with localStorage.
 */
let conversationsCache: Conversation[] = []
let isInitialized = false

/**
 * Initialize the store by loading from localStorage.
 * This should be called once on app startup.
 */
export function initializeStore(): void {
  if (isInitialized) return

  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      conversationsCache = JSON.parse(stored)
    } else {
      conversationsCache = []
    }
  } catch (error) {
    console.error("Failed to load conversations from localStorage:", error)
    conversationsCache = []
  }

  isInitialized = true
}

/**
 * Saves conversations to localStorage.
 * Called automatically after any modification.
 */
function saveToStorage(): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(conversationsCache))
  } catch (error) {
    console.error("Failed to save conversations to localStorage:", error)
  }
}

/**
 * Creates a new conversation.
 *
 * @returns The created conversation
 */
export function createConversation(): Conversation {
  const id = generateId()
  const conversation = createEmptyConversation(id)
  conversationsCache.unshift(conversation) // Add to beginning (most recent first)
  saveToStorage()
  return conversation
}

/**
 * Gets a conversation by ID.
 *
 * @param id - Conversation ID
 * @returns The conversation or undefined
 */
export function getConversation(id: string): Conversation | undefined {
  return conversationsCache.find((c) => c.id === id)
}

/**
 * Gets all conversations, sorted by updatedAt descending.
 *
 * @returns Array of conversations
 */
export function getAllConversations(): Conversation[] {
  // Return a copy to prevent accidental mutations
  return [...conversationsCache]
}

/**
 * Updates a conversation's messages and trip.
 * Automatically updates updatedAt timestamp.
 *
 * @param id - Conversation ID
 * @param updates - Partial updates (messages and/or trip)
 */
export function updateConversation(
  id: string,
  updates: {
    messages?: Message[]
    trip?: TripSummary
  },
): Conversation | undefined {
  const conversation = conversationsCache.find((c) => c.id === id)
  if (!conversation) return undefined

  if (updates.messages !== undefined) {
    conversation.messages = updates.messages
  }

  if (updates.trip !== undefined) {
    conversation.trip = updates.trip
    // Auto-generate new title based on trip
    conversation.title = generateConversationTitle(updates.trip)
  }

  // Update the timestamp
  conversation.updatedAt = new Date().toISOString()

  // Resort conversations (most recently updated first)
  conversationsCache.sort(
    (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime(),
  )

  saveToStorage()
  return conversation
}

/**
 * Deletes a conversation.
 *
 * @param id - Conversation ID
 * @returns true if deleted, false if not found
 */
export function deleteConversation(id: string): boolean {
  const index = conversationsCache.findIndex((c) => c.id === id)
  if (index === -1) return false

  conversationsCache.splice(index, 1)
  saveToStorage()
  return true
}

/**
 * Clears all conversations.
 * Use with caution!
 */
export function clearAllConversations(): void {
  conversationsCache = []
  saveToStorage()
}

/**
 * Generates a unique ID for a conversation.
 *
 * Uses timestamp + random string for uniqueness.
 * Format: "conv_" + timestamp + random
 *
 * @returns Unique ID string
 */
function generateId(): string {
  const timestamp = Date.now().toString(36)
  const random = Math.random().toString(36).substring(2, 8)
  return `conv_${timestamp}_${random}`
}

/**
 * Gets the number of conversations.
 *
 * @returns Number of conversations
 */
export function getConversationCount(): number {
  return conversationsCache.length
}

/**
 * Resets the store (useful for testing).
 */
export function resetStore(): void {
  conversationsCache = []
  isInitialized = false
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch (error) {
    console.error("Failed to clear localStorage:", error)
  }
}
