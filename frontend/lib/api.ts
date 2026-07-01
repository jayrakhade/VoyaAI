/**
 * api.ts
 *
 * HTTP client for the VoyaAI Flask backend.
 *
 * Endpoints:
 *   POST   /chat                  — Send message (creates or continues conversation)
 *   GET    /conversations         — List all conversations
 *   GET    /conversations/:id     — Get conversation with messages + trip
 *   DELETE /conversations/:id     — Delete conversation
 */

import type { TripSummary, FlightOption } from "./travel"
import type { Conversation } from "@/types/conversation"
import type { Message } from "./travel"

const BASE = "http://localhost:5000"

// ── Response types ────────────────────────────────────────────────────────────

export interface ChatResponse {
  conversationId: string
  title: string
  assistantReply: string
  trip: TripSummary
  status: string
  flights: FlightOption[]
}

export interface ConversationDetailResponse {
  conversation: Conversation
  messages: Message[]
  trip: TripSummary
}

export interface ConversationsListResponse {
  conversations: Conversation[]
  count: number
}

// ── Helpers ───────────────────────────────────────────────────────────────────

async function post<T>(path: string, body: object): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error((err as { message?: string }).message ?? `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error((err as { message?: string }).message ?? `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

async function del(path: string): Promise<void> {
  const res = await fetch(`${BASE}${path}`, { method: "DELETE" })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error((err as { message?: string }).message ?? `HTTP ${res.status}`)
  }
}

// ── API surface ───────────────────────────────────────────────────────────────

const api = {
  /**
   * Send a message. Pass conversationId to continue an existing conversation,
   * or omit/null to start a new one.
   */
  sendMessage(message: string, conversationId?: string | null): Promise<ChatResponse> {
    return post<ChatResponse>("/chat", { message, conversationId: conversationId ?? null })
  },

  /** List all conversations (sidebar). */
  getConversations(): Promise<ConversationsListResponse> {
    return get<ConversationsListResponse>("/conversations")
  },

  /** Load a single conversation with full message history and trip state. */
  getConversation(id: string): Promise<ConversationDetailResponse> {
    return get<ConversationDetailResponse>(`/conversations/${id}`)
  },

  /** Delete a conversation permanently. */
  deleteConversation(id: string): Promise<void> {
    return del(`/conversations/${id}`)
  },

  /** Health check. */
  async healthCheck(): Promise<boolean> {
    try {
      const res = await fetch(`${BASE}/health`)
      return res.ok
    } catch {
      return false
    }
  },
}

export default api
