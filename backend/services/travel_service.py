"""
services/travel_service.py

TravelService — orchestrates one complete chat turn.

This is the only entry point called by app.py.
It coordinates all other services but contains no business logic itself.

Turn flow:
  1.  Load or create Conversation from DB
  2.  Load last 10 Messages for context
  3.  Load current TripState
  4.  Call GeminiService with full context (date + history + state + message)
  5.  Convert Gemini's camelCase trip dict → snake_case for ORM
  6.  Merge into TripState via TripStateService (never overwrite valid fields)
  7.  Save user Message
  8.  Save assistant Message
  9.  Auto-update conversation title when source/destination become known
  10. Return structured response to app.py

Session strategy:
  - One DBSession per turn (opened in travel_service, passed to all services)
  - Services use db.flush() for intermediate writes (no commit)
  - save_message() commits immediately (durable message storage)
  - TripStateService.save() commits the merged trip state
  - No double-commits
"""

from typing import Any, Dict, Optional

from database import DBSession
from services.conversation_service import ConversationService
from services.trip_state_service import TripStateService
from services.gemini_service import get_gemini_service
from services.date_resolver import get_today_date


def process_chat_message(
    user_message: str,
    conversation_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Process one chat turn end-to-end.

    Args:
        user_message: Raw text from the user
        conversation_id: Existing conversation ID, or None to start new

    Returns:
        {
            "conversationId": str,
            "title":          str,
            "assistantReply": str,
            "trip":           dict  (camelCase, matches frontend TripSummary),
            "status":         str,
            "flights":        list,
        }
    """
    with DBSession() as db:

        # ── 1. Load or create conversation ───────────────────────────────────
        if conversation_id:
            conversation = ConversationService.get_conversation(db, conversation_id)
            if not conversation:
                # Stale ID from frontend — start fresh
                conversation = ConversationService.create_conversation(db)
        else:
            conversation = ConversationService.create_conversation(db)

        conv_id = conversation.id

        # ── 2. Load context ───────────────────────────────────────────────────
        history    = ConversationService.get_messages(db, conv_id, limit=10)
        trip_state = TripStateService.get_or_create(db, conv_id)
        today      = get_today_date()

        # ── 3. Call Gemini ────────────────────────────────────────────────────
        gemini      = get_gemini_service()
        ai_response = gemini.call(
            db=db,
            conv_id=conv_id,
            user_message=user_message,
            trip_state=trip_state,
            conversation_history=history,
            today_date=today,
        )

        # ── 4. Convert camelCase → snake_case for ORM ─────────────────────────
        raw_trip = ai_response.get("trip", {})
        snake_trip = {
            "source":         raw_trip.get("source", ""),
            "destination":    raw_trip.get("destination", ""),
            "departure_date": raw_trip.get("departureDate", ""),
            "return_date":    raw_trip.get("returnDate", ""),
            "budget":         raw_trip.get("budget", ""),
            "airline":        raw_trip.get("airline", ""),
            "preferred_time": raw_trip.get("preferredTime", ""),
            "status":         ai_response.get("status", ""),
        }

        # ── 5. Merge trip state (TripStateService owns this) ──────────────────
        trip_state = TripStateService.merge(db, trip_state, snake_trip)
        TripStateService.save(db, trip_state)

        # ── 6. Save messages ──────────────────────────────────────────────────
        # User message first, then assistant — preserves chronological order.
        ConversationService.save_message(db, conv_id, "user", user_message)
        ConversationService.save_message(
            db, conv_id, "assistant",
            ai_response["assistantReply"],
            flights=ai_response.get("flights", []),
        )

        # ── 7. Auto-title ─────────────────────────────────────────────────────
        # Only update when the title is still the default "New Trip".
        # Once a meaningful title is set, never overwrite it.
        if conversation.title == "New Trip":
            new_title = ConversationService.generate_conversation_title(trip_state)
            if new_title != "New Trip":
                ConversationService.update_conversation_title(db, conv_id, new_title)
                conversation.title = new_title

        # ── 8. Build response ─────────────────────────────────────────────────
        return {
            "conversationId": conv_id,
            "title":          conversation.title,
            "assistantReply": ai_response["assistantReply"],
            "trip":           trip_state.to_dict(),
            "status":         trip_state.status,
            "flights":        ai_response.get("flights", []),
        }
