"use client"

import { useEffect, useRef, useState } from "react"
import { SendHorizontal, Sparkles, Plane } from "lucide-react"
import { MessageBubble, TypingIndicator } from "@/components/travel/message-bubble"
import type { Message } from "@/lib/travel"

interface Props {
  messages: Message[]
  isThinking: boolean
  onSend: (text: string) => void
}

const suggestions = [
  "Book me a flight from Mumbai to Delhi next Friday under ₹7000",
  "Find a morning flight to Goa this weekend",
  "Cheapest non-stop from Bangalore to Dubai",
]

export function ChatPanel({ messages, isThinking, onSend }: Props) {
  const [value, setValue] = useState("")
  const composingRef = useRef(false)
  const scrollRef = useRef<HTMLDivElement>(null)
  const hasMessages = messages.length > 0

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" })
  }, [messages, isThinking])

  function submit() {
    const trimmed = value.trim()
    if (!trimmed) return
    onSend(trimmed)
    setValue("")
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    const composing = composingRef.current || e.nativeEvent.isComposing || e.keyCode === 229
    if (e.key === "Enter" && !e.shiftKey && !composing) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <section className="flex min-w-0 flex-1 flex-col bg-muted/30">
      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        <div className="mx-auto w-full max-w-3xl px-4 py-6 md:px-6">
          {!hasMessages ? (
            <div className="flex flex-col items-center py-10 text-center">
              <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-sm">
                <Plane className="h-7 w-7" aria-hidden="true" />
              </span>
              <h1 className="mt-6 text-balance text-3xl font-semibold tracking-tight text-foreground md:text-4xl">
                Book Flights with AI
              </h1>
              <p className="mt-3 max-w-xl text-pretty leading-relaxed text-muted-foreground">
                Describe your travel plans in natural language and let AI help you find and book the
                perfect flight.
              </p>

              <div className="mt-8 flex w-full max-w-xl flex-col gap-2">
                {suggestions.map((s) => (
                  <button
                    key={s}
                    onClick={() => onSend(s)}
                    className="group flex items-center gap-3 rounded-xl border border-border bg-card px-4 py-3 text-left text-sm text-foreground transition-colors hover:border-primary/40 hover:bg-accent"
                  >
                    <Sparkles className="h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
                    <span className="flex-1">{s}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="flex flex-col gap-6">
              {messages.map((m) => (
                <MessageBubble key={m.id} message={m} />
              ))}
              {isThinking && <TypingIndicator />}
            </div>
          )}
        </div>
      </div>

      <div className="border-t border-border bg-background/80 backdrop-blur-md">
        <div className="mx-auto w-full max-w-3xl px-4 py-4 md:px-6">
          <div className="flex items-end gap-2 rounded-2xl border border-border bg-card p-2 shadow-sm focus-within:border-primary/50 focus-within:ring-2 focus-within:ring-ring/20">
            <textarea
              value={value}
              onChange={(e) => setValue(e.target.value)}
              onKeyDown={handleKeyDown}
              onCompositionStart={() => (composingRef.current = true)}
              onCompositionEnd={() => (composingRef.current = false)}
              rows={1}
              placeholder="Example: Book me a flight from Mumbai to Delhi next Friday under ₹7000."
              aria-label="Describe your travel plans"
              className="max-h-40 min-h-[2.75rem] flex-1 resize-none bg-transparent px-3 py-2.5 text-sm text-foreground outline-none placeholder:text-muted-foreground"
            />
            <button
              onClick={submit}
              disabled={!value.trim() || isThinking}
              aria-label="Send message"
              className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <SendHorizontal className="h-5 w-5" aria-hidden="true" />
            </button>
          </div>
          <p className="mt-2 px-1 text-center text-xs text-muted-foreground">
            AI Travel Agent can make mistakes. Verify fares before booking.
          </p>
        </div>
      </div>
    </section>
  )
}
