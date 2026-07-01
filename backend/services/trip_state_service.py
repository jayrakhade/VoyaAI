"""
services/trip_state_service.py

TripStateService — single owner of all trip state business logic.

Responsibilities:
  - Merge new Gemini output into existing trip state (never overwrite valid fields)
  - Detect which required fields are still missing
  - Determine whether the trip is complete
  - Validate field values before persisting
  - Resolve field conflicts (e.g. user corrects a city)

Architecture position:
  TravelService → TripStateService → PostgreSQL (TripState table)

This service is the ONLY place that writes to the trip_states table.
ConversationService does NOT touch trip state.
"""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from models.conversation import TripState


# Required fields to consider a trip "complete enough to search"
REQUIRED_FIELDS = ["source", "destination", "departure_date"]


class TripStateService:
    """
    Owns all business logic for trip state management.

    Key rule: a field is only updated if the incoming value is non-empty
    AND the current stored value is empty. The only exception is when
    the user explicitly corrects a field (detected by a "change" keyword
    in the message — handled at the prompt level by Gemini returning the
    new value, which travel_service passes as allow_overwrite=True).
    """

    @staticmethod
    def get_or_create(db: Session, conv_id: str) -> TripState:
        """
        Load existing TripState for a conversation, or create a blank one.

        Args:
            db: Active SQLAlchemy session
            conv_id: Conversation ID

        Returns:
            TripState: Existing or newly created trip state
        """
        trip = db.query(TripState).filter(
            TripState.conversation_id == conv_id
        ).first()

        if not trip:
            trip = TripState(
                id=f"trip_{uuid.uuid4().hex[:12]}",
                conversation_id=conv_id,
                missing_fields=REQUIRED_FIELDS.copy(),
                status="collecting",
            )
            db.add(trip)
            db.flush()  # Assign ID without committing

        return trip

    @staticmethod
    def merge(
        db: Session,
        trip: TripState,
        new_data: dict,
        allow_overwrite: bool = False,
    ) -> TripState:
        """
        Merge new trip data into the existing TripState.

        Rules:
          1. A field is updated only if the new value is non-empty.
          2. A field is NOT overwritten if it already has a valid value,
             UNLESS allow_overwrite=True (user explicitly corrected it).
          3. missing_fields and is_complete are always recalculated
             by this service — never trusted from Gemini output.
          4. status is updated only if Gemini returns a non-empty value.

        Args:
            db: Active SQLAlchemy session
            trip: The TripState ORM object to update (already loaded)
            new_data: Snake_case dict from travel_service camelCase conversion
            allow_overwrite: If True, existing fields can be replaced

        Returns:
            TripState: The updated (but not yet committed) trip state
        """
        # Fields that map directly to ORM columns
        mergeable_fields = [
            "source",
            "destination",
            "departure_date",
            "return_date",
            "budget",
            "airline",
            "preferred_time",
        ]

        for field in mergeable_fields:
            incoming = new_data.get(field, "")
            if not incoming:
                # Gemini returned empty — keep existing value
                continue

            current = getattr(trip, field, "") or ""
            if not current or allow_overwrite:
                # Safe to write: field was empty, or explicit correction
                setattr(trip, field, incoming)

        # Recalculate missing fields and completion from actual DB state
        # (never trust Gemini's missingFields — it can hallucinate)
        trip.missing_fields = TripStateService._detect_missing(trip)
        trip.is_complete = TripStateService._is_complete(trip)

        # Update status only if Gemini provided one
        new_status = new_data.get("status", "")
        if new_status:
            trip.status = new_status
        elif trip.is_complete and trip.status == "collecting":
            trip.status = "ready_to_search"

        trip.updated_at = datetime.utcnow()
        db.flush()  # Write to session without committing

        return trip

    @staticmethod
    def _detect_missing(trip: TripState) -> list[str]:
        """
        Return list of required fields that are still empty.

        Only checks REQUIRED_FIELDS — optional fields (budget, airline,
        preferred_time, return_date) are never listed as missing.

        Args:
            trip: Current TripState

        Returns:
            list[str]: Names of empty required fields
        """
        missing = []
        field_map = {
            "source": trip.source,
            "destination": trip.destination,
            "departure_date": trip.departure_date,
        }
        for field, value in field_map.items():
            if not value or not value.strip():
                missing.append(field)
        return missing

    @staticmethod
    def _is_complete(trip: TripState) -> bool:
        """
        A trip is complete when all required fields are filled.

        Args:
            trip: Current TripState

        Returns:
            bool: True if all required fields have values
        """
        return all([
            trip.source and trip.source.strip(),
            trip.destination and trip.destination.strip(),
            trip.departure_date and trip.departure_date.strip(),
        ])

    @staticmethod
    def save(db: Session, trip: TripState) -> TripState:
        """
        Commit the trip state to the database.

        Called once per request after all merges are done.
        Separating flush (merge) from commit (save) keeps the
        session lifecycle clean.

        Args:
            db: Active SQLAlchemy session
            trip: TripState to persist

        Returns:
            TripState: Refreshed trip state after commit
        """
        db.commit()
        db.refresh(trip)
        return trip
