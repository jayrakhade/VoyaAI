"""
services/date_resolver.py

Resolves relative date expressions to ISO 8601 format (YYYY-MM-DD).

Design principle:
  Python resolves ALL dates. Gemini is never asked to calculate dates.
  The prompt injects today's date + day name so Gemini can understand
  context, but the actual resolution always happens here.

Public API:
  get_today_date()            → "2026-07-04"
  get_today_with_day_name()   → "2026-07-04 (Saturday)"
  parse_relative_date(str)    → "2026-07-05" or ""
  resolve_trip_dates(dict)    → dict with ISO dates in departureDate/returnDate
"""

from datetime import datetime, timedelta
import re


# Day name → weekday index (Monday=0 … Sunday=6)
_DAY_INDEX = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def get_today_date() -> str:
    """
    Return today's date as ISO string.

    Returns:
        str: e.g. "2026-07-04"
    """
    return datetime.now().strftime("%Y-%m-%d")


def get_today_with_day_name() -> str:
    """
    Return today's date with the day name — injected into every prompt
    so Gemini understands what "this Friday" means contextually.

    Returns:
        str: e.g. "2026-07-04 (Saturday)"
    """
    now = datetime.now()
    return f"{now.strftime('%Y-%m-%d')} ({now.strftime('%A')})"


def parse_relative_date(date_str: str, reference_date: str = None) -> str:
    """
    Convert a relative or natural-language date string to ISO format.

    Handles:
      - Already ISO: "2026-07-15"           → "2026-07-15"
      - Today:       "today"                → "2026-07-04"
      - Tomorrow:    "tomorrow"             → "2026-07-05"
      - Day name:    "friday", "saturday"   → next upcoming occurrence
      - Next + day:  "next friday"          → the friday of NEXT week
      - This + day:  "this friday"          → the friday of THIS week
      - Weekend:     "this weekend"         → coming Saturday
      - Next weekend:"next weekend"         → Saturday of next week
      - N days:      "in 3 days", "after 3 days" → +3 days
      - N weeks:     "in 2 weeks"           → +14 days
      - Next week:   "next week"            → Monday of next week

    Args:
        date_str: Input string from user or Gemini
        reference_date: ISO date to use as "today" (defaults to actual today)

    Returns:
        str: ISO date string, or "" if the input cannot be resolved
    """
    if not date_str or not date_str.strip():
        return ""

    ref = reference_date or get_today_date()
    try:
        today = datetime.strptime(ref, "%Y-%m-%d")
    except ValueError:
        return ""

    s = date_str.lower().strip()

    # ── Already ISO ──────────────────────────────────────────────────────────
    if _is_iso_date(date_str):
        return date_str

    # ── Today / Tomorrow ─────────────────────────────────────────────────────
    if s == "today" or s.startswith("today"):
        return today.strftime("%Y-%m-%d")

    if "tomorrow" in s:
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")

    # ── Next week (Monday of next week) ──────────────────────────────────────
    if re.search(r"\bnext\s+week\b", s):
        days_to_monday = (7 - today.weekday()) % 7 or 7
        return (today + timedelta(days=days_to_monday)).strftime("%Y-%m-%d")

    # ── Weekend ───────────────────────────────────────────────────────────────
    if "weekend" in s:
        # "weekend" → coming Saturday (or next Saturday if already Sat/Sun + "next")
        current_wd = today.weekday()  # 0=Mon … 6=Sun
        days_to_sat = (5 - current_wd) % 7  # Saturday = 5

        if "next" in s:
            # Explicitly "next weekend" → always the Saturday of NEXT week
            days_to_sat = days_to_sat if days_to_sat > 0 else 7
            if current_wd >= 5:  # Already on weekend
                days_to_sat += 7
        else:
            # "this weekend" or just "weekend" → nearest upcoming Saturday
            if days_to_sat == 0:
                days_to_sat = 7  # Today is Saturday → next Saturday

        return (today + timedelta(days=days_to_sat)).strftime("%Y-%m-%d")

    # ── Named day of week ─────────────────────────────────────────────────────
    for day_name, target_wd in _DAY_INDEX.items():
        if day_name in s:
            current_wd = today.weekday()
            days_ahead = (target_wd - current_wd) % 7

            if "next" in s:
                # "next friday" → always at least 7 days away
                if days_ahead == 0:
                    days_ahead = 7
                else:
                    days_ahead += 7
            elif "this" in s:
                # "this friday" → the friday of the current calendar week
                # If that day has already passed this week, go to next week
                if days_ahead == 0:
                    days_ahead = 7  # Same day → next occurrence
            else:
                # Bare "friday" → nearest upcoming occurrence (never today, never past)
                if days_ahead == 0:
                    days_ahead = 7  # Same weekday → next week

            return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

    # ── "In/After N days" ─────────────────────────────────────────────────────
    m = re.search(r"(?:in|after)\s+(\d+)\s+days?", s)
    if m:
        return (today + timedelta(days=int(m.group(1)))).strftime("%Y-%m-%d")

    # ── "In N weeks" ─────────────────────────────────────────────────────────
    m = re.search(r"in\s+(\d+)\s+weeks?", s)
    if m:
        return (today + timedelta(weeks=int(m.group(1)))).strftime("%Y-%m-%d")

    # ── Cannot resolve ────────────────────────────────────────────────────────
    return ""


def resolve_trip_dates(trip_data: dict, reference_date: str = None) -> dict:
    """
    Resolve departureDate and returnDate fields in a camelCase trip dict.

    Called after Gemini responds as a safety net — if Gemini returned
    a relative string instead of ISO, this converts it.
    If Gemini already returned ISO, parse_relative_date returns it unchanged.

    Args:
        trip_data: camelCase trip dict from Gemini
        reference_date: ISO date to use as "today"

    Returns:
        dict: Same dict with date fields resolved to ISO format
    """
    for field in ("departureDate", "returnDate"):
        val = trip_data.get(field, "")
        if val:
            resolved = parse_relative_date(val, reference_date)
            # Only replace if we successfully resolved it
            # (don't blank out a value we couldn't parse)
            if resolved:
                trip_data[field] = resolved

    return trip_data


def _is_iso_date(s: str) -> bool:
    """Return True if s is a valid YYYY-MM-DD string."""
    try:
        datetime.strptime(s.strip(), "%Y-%m-%d")
        return True
    except ValueError:
        return False
