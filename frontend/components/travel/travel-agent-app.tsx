"use client"

import { useCallback, useEffect, useState } from "react"
import { TopNav } from "@/components/travel/top-nav"
import { ConversationSidebar } from "@/components/travel/conversation-sidebar"
import { ChatPanel } from "@/components/travel/chat-panel"
import { SummaryPanel } from "@/components/travel/summary-panel"
import { emptyTrip, type Message, type TripSummary } from "@/lib/travel"
import chatService from "@/services/chatService"
import type { Conversation } from "@/types/conversation"

export function TravelAgentApp() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeId, setActiveId] = useState<string | undefined>(undefined)
  const [messages, setMessages] = useState<Message[]>([])
  const [trip, setTrip] = useState<TripSummary>(emptyTrip)
  const [isThinking, setIsThinking] = useState(false)
  const [isLoaded, setIsLoaded] = useState(false)

  // ── Load sidebar conversations from backend on mount ──────────────────────
  useEffect(() => {
    chatService.getConversations()
      .then(({ conversations: list }) => {
        setConversations(list)
        // Auto-select the most recent conversation
        if (list.length > 0) setActiveId(list[0].id)
      })
      .catch(console.error)
      .finally(() => setIsLoaded(true))
  }, [])

  // ── Load full conversation when user switches ─────────────────────────────
  useEffect(() => {
    if (!activeId) return
    chatService.getConversation(activeId)
      .then(({ messages: msgs, trip: t }) => {
        setMessages(msgs.map(m => ({
          id: (m as Message & { id?: string }).id ?? crypto.randomUUID(),
          role: m.role,
          content: m.content,
          flights: m.flights,
        })))
        setTrip(t ?? emptyTrip)
      })
      .catch(console.error)
  }, [activeId])

  // ── Send message ──────────────────────────────────────────────────────────
  const handleSend = useCallback(async (text: string) => {
    // Optimistically add user message
    const userMsg: Message = { id: crypto.randomUUID(), role: "user", content: text }
    setMessages(prev => [...prev, userMsg])
    setIsThinking(true)

    try {
      const response = await chatService.chat(text, activeId ?? null)

      // If this was a new conversation, add it to the top of the sidebar
      if (!activeId || activeId !== response.conversationId) {
        setActiveId(response.conversationId)
        // Add the new conversation to the top of the sidebar immediately,
        // then refresh from backend to get the accurate message_count
        setConversations(prev => [
          {
            id: response.conversationId,
            title: response.title,
            status: response.status,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            message_count: 2,
          },
          ...prev.filter(c => c.id !== response.conversationId),
        ])
      } else {
        // Update title + updated_at + message_count in sidebar
        setConversations(prev =>
          prev.map(c => c.id === response.conversationId
            ? {
                ...c,
                title: response.title,
                updated_at: new Date().toISOString(),
                message_count: c.message_count + 2, // user + assistant
              }
            : c
          )
        )
      }

      setTrip(response.trip)
      setMessages(prev => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: response.assistantReply,
          flights: response.flights,
        },
      ])
    } catch (error) {
      const msg = error instanceof Error ? error.message : "Failed to process your request"
      setMessages(prev => [
        ...prev,
        { id: crypto.randomUUID(), role: "assistant", content: `Error: ${msg}. Please try again.`, flights: [] },
      ])
    } finally {
      setIsThinking(false)
    }
  }, [activeId])

  // ── New chat ──────────────────────────────────────────────────────────────
  const handleNewChat = useCallback(() => {
    setActiveId(undefined)
    setMessages([])
    setTrip(emptyTrip)
    setIsThinking(false)
  }, [])

  // ── Select conversation ───────────────────────────────────────────────────
  const handleSelect = useCallback((id: string) => {
    if (id === activeId) return
    setMessages([])
    setTrip(emptyTrip)
    setActiveId(id)
  }, [activeId])

  // ── Delete conversation ───────────────────────────────────────────────────
  const handleDelete = useCallback(async (id: string) => {
    try {
      await chatService.deleteConversation(id)
      const updated = conversations.filter(c => c.id !== id)
      setConversations(updated)
      if (id === activeId) {
        if (updated.length > 0) {
          handleSelect(updated[0].id)
        } else {
          handleNewChat()
        }
      }
    } catch (error) {
      console.error("Failed to delete conversation:", error)
    }
  }, [activeId, conversations, handleSelect, handleNewChat])

  // ── Search (placeholder) ──────────────────────────────────────────────────
  const handleSearch = useCallback(() => {
    handleSend("Search flights with the current trip details.")
  }, [handleSend])

  if (!isLoaded) {
    return (
      <div className="flex h-dvh items-center justify-center bg-background">
        <div className="text-muted-foreground">Loading conversations...</div>
      </div>
    )
  }

  return (
    <div className="flex h-dvh flex-col overflow-hidden bg-background">
      <TopNav />
      <div className="flex min-h-0 flex-1">
        <ConversationSidebar
          conversations={conversations}
          activeId={activeId}
          onSelect={handleSelect}
          onNewChat={handleNewChat}
          onDelete={handleDelete}
        />
        <ChatPanel messages={messages} isThinking={isThinking} onSend={handleSend} />
        <SummaryPanel trip={trip} onSearch={handleSearch} isThinking={isThinking} />
      </div>
    </div>
  )
}
