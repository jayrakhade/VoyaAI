"use client"

import {
  MapPin,
  Navigation,
  CalendarDays,
  CalendarCheck,
  Wallet,
  Plane,
  Clock,
  Search,
} from "lucide-react"
import type { TripSummary } from "@/lib/travel"

interface Props {
  trip: TripSummary
  onSearch: () => void
  isThinking: boolean
}

function Field({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: string
}) {
  const filled = value.trim().length > 0
  return (
    <div className="flex items-center gap-3 rounded-xl border border-border bg-background px-3 py-3">
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-accent text-accent-foreground">
        <Icon className="h-4 w-4" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium text-muted-foreground">{label}</p>
        <p className={filled ? "truncate text-sm font-semibold text-foreground" : "text-sm text-muted-foreground/60"}>
          {filled ? value : "Not set"}
        </p>
      </div>
    </div>
  )
}

export function SummaryPanel({ trip, onSearch, isThinking }: Props) {
  return (
    <aside className="hidden w-80 shrink-0 flex-col border-l border-border bg-sidebar xl:flex">
      <div className="flex-1 overflow-y-auto p-5">
        <div className="mb-4">
          <h2 className="text-base font-semibold text-foreground">Travel Summary</h2>
          <p className="text-sm text-muted-foreground">Details extracted from your chat</p>
        </div>

        <div className="flex flex-col gap-2.5">
          <Field icon={MapPin} label="Source" value={trip.source} />
          <Field icon={Navigation} label="Destination" value={trip.destination} />
          <Field icon={CalendarDays} label="Departure Date" value={trip.departureDate} />
          <Field icon={CalendarCheck} label="Return Date" value={trip.returnDate} />
          <Field icon={Wallet} label="Budget" value={trip.budget} />
          <Field icon={Plane} label="Preferred Airline" value={trip.airline} />
          <Field icon={Clock} label="Preferred Time" value={trip.preferredTime} />
        </div>
      </div>

      <div className="border-t border-border p-5">
        <button
          onClick={onSearch}
          disabled={isThinking}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground shadow-sm transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Search className="h-4 w-4" aria-hidden="true" />
          Search Flights
        </button>
      </div>
    </aside>
  )
}
