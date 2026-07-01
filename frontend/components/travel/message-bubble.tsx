"use client"

import { Plane, Sparkles, ArrowRight, Clock } from "lucide-react"
import { cn } from "@/lib/utils"
import type { Message } from "@/lib/travel"

function FlightCard({
  airline,
  flightNo,
  depart,
  arrive,
  duration,
  stops,
  price,
}: NonNullable<Message["flights"]>[number]) {
  return (
    <div className="flex items-center gap-4 rounded-xl border border-border bg-background p-3.5 transition-shadow hover:shadow-sm">
      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent text-accent-foreground">
        <Plane className="h-5 w-5" aria-hidden="true" />
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="truncate text-sm font-semibold text-foreground">{airline}</p>
          <span className="text-xs text-muted-foreground">{flightNo}</span>
        </div>
        <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-foreground">
          <span className="font-medium">{depart}</span>
          <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" aria-hidden="true" />
          <span className="font-medium">{arrive}</span>
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            <Clock className="h-3 w-3" aria-hidden="true" />
            {duration} · {stops}
          </span>
        </div>
      </div>
      <div className="shrink-0 text-right">
        <p className="text-base font-semibold text-foreground">{price}</p>
        <button className="mt-1 rounded-md bg-primary px-2.5 py-1 text-xs font-semibold text-primary-foreground transition-colors hover:bg-primary/90">
          Select
        </button>
      </div>
    </div>
  )
}

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user"

  return (
    <div className={cn("flex w-full gap-3", isUser ? "justify-end" : "justify-start")}>
      {!isUser && (
        <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
          <Sparkles className="h-4 w-4" aria-hidden="true" />
        </span>
      )}

      <div className={cn("flex max-w-[85%] flex-col gap-3 md:max-w-[75%]", isUser && "items-end")}>
        <div
          className={cn(
            "rounded-2xl px-4 py-3 text-sm leading-relaxed",
            isUser
              ? "rounded-br-md bg-primary text-primary-foreground"
              : "rounded-bl-md border border-border bg-card text-card-foreground",
          )}
        >
          {message.content}
        </div>

        {message.flights && message.flights.length > 0 && (
          <div className="flex w-full flex-col gap-2">
            {message.flights.map((f) => (
              <FlightCard key={f.flightNo} {...f} />
            ))}
          </div>
        )}
      </div>

      {isUser && (
        <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-accent text-sm font-semibold text-accent-foreground">
          You
        </span>
      )}
    </div>
  )
}

export function TypingIndicator() {
  return (
    <div className="flex w-full items-start gap-3">
      <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
        <Sparkles className="h-4 w-4" aria-hidden="true" />
      </span>
      <div className="flex items-center gap-1.5 rounded-2xl rounded-bl-md border border-border bg-card px-4 py-4">
        <span className="sr-only">AI is thinking</span>
        <Dot delay="0ms" />
        <Dot delay="150ms" />
        <Dot delay="300ms" />
      </div>
    </div>
  )
}

function Dot({ delay }: { delay: string }) {
  return (
    <span
      className="h-2 w-2 animate-bounce rounded-full bg-primary/60"
      style={{ animationDelay: delay, animationDuration: "1s" }}
    />
  )
}
