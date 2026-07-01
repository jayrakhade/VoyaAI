"""
services/prompt_builder.py

Dynamic prompt building with conversation context.

Purpose:
- Build prompts that include full conversation history
- Include current trip state
- Include today's date for date resolution
- Prevent Gemini from forgetting context

Example prompt:
```
Today's Date: 2026-07-01

Current Trip State
Source: (empty)
Destination: (empty)
Departure Date: (empty)
Budget: (empty)

Conversation History
User: Need flight from Nagpur to Raipur
Assistant: When would you like to travel?
User: Tomorrow

Current Message: Tomorrow

Instructions:
...
```
"""

from datetime import datetime
from models.conversation import Message, TripState
from services.date_resolver import get_today_date, get_today_with_day_name


class PromptBuilder:
    """Builds context-aware prompts for Gemini."""
    
    @staticmethod
    def build_chat_prompt(
        current_message: str,
        trip_state: TripState,
        conversation_history: list[Message],
        today_date: str = None
    ) -> str:
        """
        Build complete prompt with context for Gemini.

        Sections:
          1. Today's date + day name  (for relative date resolution)
          2. Current trip state       (what we already know — never erase)
          3. Conversation history     (last 10 messages for context)
          4. Current user message     (what the user just said)
          5. Instructions             (merge rules + JSON format)

        Args:
            current_message: User's current message
            trip_state: Current trip state from database
            conversation_history: List of recent messages (last 10)
            today_date: Today's date ISO string (auto if None)

        Returns:
            str: Complete prompt for Gemini
        """
        today_with_day = get_today_with_day_name()

        parts = []

        # ── 1. Date context ──────────────────────────────────────────────────
        parts.append(f"Today's Date: {today_with_day}")
        parts.append("")

        # ── 2. Current trip state ────────────────────────────────────────────
        # Show the FULL current state so Gemini knows what is already known.
        # Gemini must echo back ALL fields (filled + empty) in its response.
        parts.append("=== CURRENT TRIP STATE (already collected) ===")
        parts.append(f"Source:         {trip_state.source or '(not yet provided)'}")
        parts.append(f"Destination:    {trip_state.destination or '(not yet provided)'}")
        parts.append(f"Departure Date: {trip_state.departure_date or '(not yet provided)'}")
        parts.append(f"Return Date:    {trip_state.return_date or '(not yet provided)'}")
        parts.append(f"Budget:         {trip_state.budget or '(not yet provided)'}")
        parts.append(f"Airline:        {trip_state.airline or '(not yet provided)'}")
        parts.append(f"Preferred Time: {trip_state.preferred_time or '(not yet provided)'}")
        parts.append("")

        # ── 3. Conversation history ──────────────────────────────────────────
        if conversation_history:
            parts.append("=== CONVERSATION HISTORY (last messages) ===")
            for msg in conversation_history:
                role = "User" if msg.role == "user" else "Assistant"
                parts.append(f"{role}: {msg.content}")
            parts.append("")

        # ── 4. Current message ───────────────────────────────────────────────
        parts.append("=== CURRENT USER MESSAGE ===")
        parts.append(current_message)
        parts.append("")

        # ── 5. Instructions ──────────────────────────────────────────────────
        parts.append("=== INSTRUCTIONS ===")
        parts.append(PromptBuilder._instructions())

        return "\n".join(parts)
    
    @staticmethod
    def _instructions() -> str:
        """
        Inline instructions appended to every prompt.

        These reinforce the system prompt rules at the prompt level.
        Critical rules:
          - Echo back ALL trip fields (filled and empty) in the response
          - Never blank out a field that already has a value
          - Resolve relative dates using Today's Date shown above
          - Return ONLY valid JSON — no markdown, no explanation
        """
        return """RULES (follow exactly):
1. Read the CURRENT TRIP STATE above carefully.
2. Extract any NEW information from the CURRENT USER MESSAGE.
3. In your JSON response, echo back ALL trip fields:
   - For fields that already have a value: keep that exact value.
   - For fields the user just provided: use the new value.
   - For fields still unknown: use empty string "".
4. NEVER return an empty string for a field that already has a value.
5. Resolve relative dates (Tomorrow, Next Friday, etc.) using Today's Date.
   Return dates as YYYY-MM-DD. If you cannot resolve, return empty string.
6. Ask only for the NEXT missing required field (source, destination, departure_date).
7. Return ONLY valid JSON. No markdown. No code blocks. No explanation.

Required JSON format:
{
  "assistantReply": "your conversational message to the user",
  "trip": {
    "source": "city or empty string",
    "destination": "city or empty string",
    "departureDate": "YYYY-MM-DD or empty string",
    "returnDate": "YYYY-MM-DD or empty string",
    "budget": "e.g. ₹7000 or empty string",
    "airline": "airline name or empty string",
    "preferredTime": "Morning/Afternoon/Evening/Night or empty string"
  },
  "status": "collecting",
  "flights": []
}"""
    
