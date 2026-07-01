"""
services/conversation_service.py

ConversationService — owns conversation and message CRUD only.

Responsibilities:
  - Create conversation
  - Load conversation (single + list)
  - Save message (user or assistant)
  - Load messages (last N, chronological)
  - Generate conversation title from trip state
  - Update conversation title
  - Delete conversation

NOT responsible for:
  - Trip state merge logic  → TripStateService
  - AI calls                → GeminiService
  - Orchestration           → TravelService

Database is the single source of truth.
Frontend localStorage is a UI cache only.
"""

import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from models.conversation import Conversation, Message, TripState


class ConversationService:

    @staticmethod
    def create_conversation(db: Session, title: str = "New Trip") -> Conversation:
        """
        Create a new conversation row and its associated blank TripState.

        Both are flushed together in one commit so they are always in sync.

        Args:
            db: Active SQLAlchemy session
            title: Initial title (default "New Trip", updated later)

        Returns:
            Conversation: The persisted conversation object
        """
        conv_id = f"conv_{uuid.uuid4().hex[:12]}"

        conversation = Conversation(
            id=conv_id,
            title=title,
            status="collecting",
        )
        trip_state = TripState(
            id=f"trip_{uuid.uuid4().hex[:12]}",
            conversation_id=conv_id,
            missing_fields=["source", "destination", "departure_date"],
            status="collecting",
        )
        conversation.trip_state = trip_state

        db.add(conversation)
        db.add(trip_state)
        db.commit()
        db.refresh(conversation)

        return conversation

    @staticmethod
    def get_conversation(db: Session, conv_id: str) -> Conversation | None:
        """
        Load a conversation by ID.

        Args:
            db: Active SQLAlchemy session
            conv_id: Conversation primary key

        Returns:
            Conversation or None if not found
        """
        return db.query(Conversation).filter(Conversation.id == conv_id).first()

    @staticmethod
    def get_all_conversations(db: Session) -> list[Conversation]:
        """
        Return all conversations ordered by most recently updated first.

        Uses a subquery to get message_count without loading all messages
        (avoids N+1 queries on the sidebar list).

        Args:
            db: Active SQLAlchemy session

        Returns:
            list[Conversation]: Ordered by updated_at DESC
        """
        from sqlalchemy import func
        from models.conversation import Message as Msg

        # Subquery: count messages per conversation
        msg_count = (
            db.query(
                Msg.conversation_id,
                func.count(Msg.id).label("cnt"),
            )
            .group_by(Msg.conversation_id)
            .subquery()
        )

        rows = (
            db.query(Conversation, msg_count.c.cnt)
            .outerjoin(msg_count, Conversation.id == msg_count.c.conversation_id)
            .order_by(Conversation.updated_at.desc())
            .all()
        )

        # Attach count to each conversation object so to_dict() can use it
        result = []
        for conv, cnt in rows:
            conv._message_count = cnt or 0
            result.append(conv)
        return result

    @staticmethod
    def save_message(
        db: Session,
        conv_id: str,
        role: str,
        content: str,
        flights: list = None,
    ) -> Message:
        """
        Persist a single message and bump the conversation's updated_at.

        Commits immediately so the message is durable before the next
        operation. This is safe because DBSession no longer auto-commits.

        Args:
            db: Active SQLAlchemy session
            conv_id: Parent conversation ID
            role: "user" or "assistant"
            content: Message text
            flights: Optional list of flight dicts (assistant messages only)

        Returns:
            Message: The persisted message object
        """
        message = Message(
            id=f"msg_{uuid.uuid4().hex[:12]}",
            conversation_id=conv_id,
            role=role,
            content=content,
            flights=flights or [],
        )
        db.add(message)

        # Bump updated_at so the sidebar sorts correctly
        conversation = db.query(Conversation).filter(
            Conversation.id == conv_id
        ).first()
        if conversation:
            conversation.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(message)

        return message

    @staticmethod
    def get_messages(db: Session, conv_id: str, limit: int = 10) -> list[Message]:
        """
        Return the most recent `limit` messages in chronological order.

        Fetches DESC (newest first) then reverses in Python so Gemini
        receives messages oldest → newest, which is the natural reading order.

        Args:
            db: Active SQLAlchemy session
            conv_id: Conversation ID
            limit: Maximum number of messages to return (default 10)

        Returns:
            list[Message]: Messages in ascending timestamp order
        """
        rows = (
            db.query(Message)
            .filter(Message.conversation_id == conv_id)
            .order_by(Message.timestamp.desc())
            .limit(limit)
            .all()
        )
        return list(reversed(rows))

    @staticmethod
    def get_trip_state(db: Session, conv_id: str) -> TripState | None:
        """
        Load the TripState for a conversation.

        Args:
            db: Active SQLAlchemy session
            conv_id: Conversation ID

        Returns:
            TripState or None
        """
        return (
            db.query(TripState)
            .filter(TripState.conversation_id == conv_id)
            .first()
        )

    @staticmethod
    def generate_conversation_title(trip_state: TripState) -> str:
        """
        Derive a human-readable title from the current trip state.

        Rules (in priority order):
          source + destination  → "Mumbai → Delhi"
          destination only      → "Goa Trip"
          neither               → "New Trip"

        Args:
            trip_state: Current TripState object

        Returns:
            str: Generated title
        """
        src = (trip_state.source or "").strip()
        dst = (trip_state.destination or "").strip()

        if src and dst:
            return f"{src} → {dst}"
        if dst:
            return f"{dst} Trip"
        return "New Trip"

    @staticmethod
    def update_conversation_title(
        db: Session, conv_id: str, title: str
    ) -> Conversation | None:
        """
        Persist a new title for a conversation.

        Args:
            db: Active SQLAlchemy session
            conv_id: Conversation ID
            title: New title string

        Returns:
            Updated Conversation or None if not found
        """
        conversation = db.query(Conversation).filter(
            Conversation.id == conv_id
        ).first()
        if conversation:
            conversation.title = title
            conversation.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(conversation)
        return conversation

    @staticmethod
    def delete_conversation(db: Session, conv_id: str) -> bool:
        """
        Delete a conversation and all its related data (cascade).

        Messages and TripState are deleted automatically via
        the cascade="all, delete-orphan" relationship on Conversation.

        Args:
            db: Active SQLAlchemy session
            conv_id: Conversation ID

        Returns:
            bool: True if deleted, False if not found
        """
        conversation = db.query(Conversation).filter(
            Conversation.id == conv_id
        ).first()
        if conversation:
            db.delete(conversation)
            db.commit()
            return True
        return False
