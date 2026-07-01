"use client"

import { MessageSquare, Plus, Search, Trash2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { formatRelativeTime } from "@/types/conversation"
import type { Conversation } from "@/types/conversation"
// Backend returns snake_case timestamps; message_count instead of messages array

interface Props {
  conversations: Conversation[]
  activeId: string | undefined
  onSelect: (id: string) => void
  onNewChat: () => void
  onDelete: (id: string) => void
}

export function ConversationSidebar({
  conversations,
  activeId,
  onSelect,
  onNewChat,
  onDelete,
}: Props) {
  return (
    <aside className="hidden w-72 shrink-0 flex-col border-r border-sidebar-border bg-sidebar lg:flex">
      <div className="p-4">
        <button
          onClick={onNewChat}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground shadow-sm transition-colors hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" aria-hidden="true" />
          New trip
        </button>
      </div>

      <div className="px-4 pb-2">
        <div className="flex items-center gap-2 rounded-lg border border-sidebar-border bg-background px-3 py-2">
          <Search className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
          <input
            type="search"
            placeholder="Search trips"
            className="w-full bg-transparent text-sm text-foreground outline-none placeholder:text-muted-foreground"
            aria-label="Search conversations"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-2">
        <p className="px-2 pb-2 pt-1 text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Recent
        </p>
        <ul className="flex flex-col gap-1">
          {conversations.length === 0 ? (
            <li className="px-2 py-4 text-center text-xs text-muted-foreground">
              No conversations yet
            </li>
          ) : (
            conversations.map((c) => (
              <li key={c.id} className="group">
                <div
                  className={cn(
                    "flex w-full items-start gap-3 rounded-xl px-3 py-2.5 transition-colors",
                    c.id === activeId
                      ? "bg-sidebar-accent text-sidebar-accent-foreground"
                      : "text-sidebar-foreground hover:bg-sidebar-accent/60",
                  )}
                >
                  <button
                    onClick={() => onSelect(c.id)}
                    className="min-w-0 flex-1 text-left"
                  >
                    <MessageSquare
                      className="mb-1 h-4 w-4 inline-block mr-2 shrink-0 text-primary"
                      aria-hidden="true"
                    />
                    <span className="block truncate text-sm font-medium">{c.title}</span>
                    <span className="block truncate text-xs text-muted-foreground">
                      {c.message_count > 0 ? `${c.message_count} message${c.message_count !== 1 ? "s" : ""}` : "No messages yet"}
                    </span>
                  </button>

                  <div className="flex items-center gap-1 shrink-0">
                    <span className="text-[10px] text-muted-foreground whitespace-nowrap">
                      {formatRelativeTime(c.updated_at)}
                    </span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        if (confirm("Delete this conversation?")) {
                          onDelete(c.id)
                        }
                      }}
                      className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-destructive/10 rounded text-destructive hover:text-destructive"
                      aria-label="Delete conversation"
                      title="Delete"
                    >
                      <Trash2 className="h-3 w-3" aria-hidden="true" />
                    </button>
                  </div>
                </div>
              </li>
            ))
          )}
        </ul>
      </div>

      <div className="border-t border-sidebar-border p-4">
        <div className="flex items-center gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-accent text-sm font-semibold text-accent-foreground">
            AV
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-foreground">Ava Traveler</p>
            <p className="truncate text-xs text-muted-foreground">Free plan</p>
          </div>
        </div>
      </div>
    </aside>
  )
}
