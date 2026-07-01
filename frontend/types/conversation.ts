/**
 * types/conversation.ts
 *
 * Conversation types that mirror the backend response shape.
 * localStorage is only used as a UI cache — PostgreSQL is the source of truth.
 */

import type { Message, TripSummary } from "@/lib/travel"

export interface Conversation {
  id: string
  title: string
  status: string
  created_at: string
  updated_at: string
  message_count: number
  // Loaded on demand (GET /conversations/:id)
  messages?: Message[]
  trip?: TripSummary
}

/**
 * Format a date string for sidebar display.
 *
 * Examples: "2m ago", "1h ago", "Yesterday", "Jul 1"
 */
export function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return "Just now"
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays === 1) return "Yesterday"
  if (diffDays < 7) return `${diffDays}d ago`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`

  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" })
}
