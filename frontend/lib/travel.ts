export type Role = "user" | "assistant"

export interface Message {
  id: string
  role: Role
  content: string
  flights?: FlightOption[]
}

export interface TripSummary {
  source: string
  destination: string
  departureDate: string
  returnDate: string
  budget: string
  airline: string
  preferredTime: string
}

export interface FlightOption {
  airline: string
  flightNo: string
  depart: string
  arrive: string
  duration: string
  stops: string
  price: string
}

export const emptyTrip: TripSummary = {
  source: "",
  destination: "",
  departureDate: "",
  returnDate: "",
  budget: "",
  airline: "",
  preferredTime: "",
}

function titleCase(value: string) {
  return value
    .trim()
    .split(/\s+/)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(" ")
}

/**
 * Very lightweight natural-language parser used to populate the trip summary.
 * This is a front-end demo, so it uses simple heuristics rather than a real model.
 */
export function parseTrip(text: string, base: TripSummary): TripSummary {
  const next: TripSummary = { ...base }
  const lower = text.toLowerCase()

  const fromTo = lower.match(/from\s+([a-z\s]+?)\s+to\s+([a-z\s]+?)(?:\s+(?:on|next|under|around|by|for|with|in|,|\.|$))/)
  if (fromTo) {
    next.source = titleCase(fromTo[1])
    next.destination = titleCase(fromTo[2])
  } else {
    const toOnly = lower.match(/\bto\s+([a-z\s]+?)(?:\s+(?:on|next|under|around|by|for|with|in|,|\.|$))/)
    if (toOnly) next.destination = titleCase(toOnly[1])
  }

  const day = lower.match(/next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)/)
  if (day) next.departureDate = `Next ${titleCase(day[1])}`
  const explicitDate = text.match(/\b(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+|[A-Za-z]+\s+\d{1,2})\b/)
  if (!next.departureDate && explicitDate) next.departureDate = explicitDate[1]

  const budget = text.match(/(?:under|below|less than|max|budget of|around)\s*[₹$€]?\s?([\d,]+)/i)
  if (budget) {
    const symbol = text.includes("$") ? "$" : text.includes("€") ? "€" : "₹"
    next.budget = `${symbol}${budget[1].replace(/,/g, "")}`
  }

  const airlines = ["indigo", "air india", "vistara", "spicejet", "emirates", "lufthansa", "united", "delta"]
  const foundAirline = airlines.find((a) => lower.includes(a))
  if (foundAirline) next.airline = titleCase(foundAirline)

  if (/\bmorning\b/.test(lower)) next.preferredTime = "Morning"
  else if (/\bafternoon\b/.test(lower)) next.preferredTime = "Afternoon"
  else if (/\bevening\b/.test(lower)) next.preferredTime = "Evening"
  else if (/\bnight\b|\bred[-\s]?eye\b/.test(lower)) next.preferredTime = "Night"

  if (/round\s?trip|return/.test(lower) && !next.returnDate) {
    next.returnDate = "Flexible"
  }

  return next
}

export function buildAssistantReply(trip: TripSummary): { content: string; flights: FlightOption[] } {
  const route =
    trip.source && trip.destination
      ? `${trip.source} → ${trip.destination}`
      : trip.destination
        ? `your trip to ${trip.destination}`
        : "your trip"

  const flights: FlightOption[] = [
    {
      airline: trip.airline || "IndiGo",
      flightNo: "6E 2043",
      depart: "06:20",
      arrive: "08:15",
      duration: "1h 55m",
      stops: "Non-stop",
      price: trip.budget || "₹5,499",
    },
    {
      airline: "Vistara",
      flightNo: "UK 981",
      depart: "11:40",
      arrive: "13:50",
      duration: "2h 10m",
      stops: "Non-stop",
      price: "₹6,240",
    },
    {
      airline: "Air India",
      flightNo: "AI 866",
      depart: "18:05",
      arrive: "20:30",
      duration: "2h 25m",
      stops: "Non-stop",
      price: "₹6,980",
    },
  ]

  const content = `Great — I found some options for ${route}. Here are the best matches based on your budget and preferred time. I've also updated the trip summary on the right. Want me to hold a seat or refine the search?`

  return { content, flights }
}
