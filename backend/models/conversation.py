"""
models/conversation.py

Database models for VoyaAI conversations using SQLAlchemy ORM.

Models:
- Conversation: Trip planning session metadata
- Message: Individual messages in conversation history
- TripState: Current travel details and state

Architecture:
Each Conversation has one TripState (1:1)
Each Conversation has many Messages (1:N)
"""

from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Conversation(Base):
    """
    Represents a trip planning conversation session.
    
    Attributes:
        id: Unique conversation identifier
        title: Auto-generated title (e.g., "Mumbai → Delhi", "Goa Trip")
        status: Current state ('collecting', 'completed', 'archived')
        created_at: When conversation started
        updated_at: Last activity timestamp
        messages: List of Message objects (relationship)
        trip_state: Associated TripState object (relationship)
    """
    
    __tablename__ = "conversations"
    
    id = Column(String(50), primary_key=True)
    title = Column(String(200), nullable=False, default="New Trip")
    status = Column(String(50), nullable=False, default="collecting")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    trip_state = relationship("TripState", back_populates="conversation", uselist=False, cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        # _message_count is set by get_all_conversations() to avoid N+1 queries.
        # For single-conversation loads, fall back to len(self.messages).
        count = getattr(self, "_message_count", None)
        if count is None:
            count = len(self.messages)
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "message_count": count,
        }


class Message(Base):
    """
    Represents a single message in conversation history.
    
    Attributes:
        id: Unique message identifier
        conversation_id: Foreign key to parent conversation
        role: "user" or "assistant"
        content: Message text
        flights: JSON array of flight options (if assistant message)
        timestamp: When message was created
    """
    
    __tablename__ = "messages"
    
    id = Column(String(50), primary_key=True)
    conversation_id = Column(String(50), ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    flights = Column(JSON, nullable=True, default=[])
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationship
    conversation = relationship("Conversation", back_populates="messages")
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "flights": self.flights or [],
            "timestamp": self.timestamp.isoformat(),
        }


class TripState(Base):
    """
    Represents the current travel request state for a conversation.
    
    This is the SINGLE SOURCE OF TRUTH for trip information.
    Never overwrites existing valid fields.
    
    Attributes:
        id: Unique trip state identifier
        conversation_id: Foreign key to parent conversation (unique)
        source: Departure city
        destination: Arrival city
        departure_date: Travel date (ISO format or relative like "Tomorrow")
        return_date: Return date (if round trip)
        budget: Budget with currency (e.g., "₹7000", "$500")
        airline: Preferred airline
        preferred_time: Preferred departure time ("Morning", "Afternoon", etc)
        missing_fields: List of fields still needed from user
        is_complete: True when all required fields collected
        status: "collecting", "ready_to_search", "booked"
        updated_at: Last update timestamp
    """
    
    __tablename__ = "trip_states"
    
    id = Column(String(50), primary_key=True)
    conversation_id = Column(String(50), ForeignKey("conversations.id"), unique=True, nullable=False)
    
    # Trip details
    source = Column(String(100), default="")
    destination = Column(String(100), default="")
    departure_date = Column(String(100), default="")
    return_date = Column(String(100), default="")
    budget = Column(String(100), default="")
    airline = Column(String(100), default="")
    preferred_time = Column(String(50), default="")
    
    # State tracking
    missing_fields = Column(JSON, default=[])  # ["source", "departure_date", "budget"]
    is_complete = Column(Boolean, default=False)
    status = Column(String(50), default="collecting")  # collecting, ready_to_search, booked
    
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    conversation = relationship("Conversation", back_populates="trip_state")
    
    def to_dict(self):
        """Convert to camelCase dictionary for JSON serialization."""
        return {
            "source": self.source or "",
            "destination": self.destination or "",
            "departureDate": self.departure_date or "",
            "returnDate": self.return_date or "",
            "budget": self.budget or "",
            "airline": self.airline or "",
            "preferredTime": self.preferred_time or "",
            "missingFields": self.missing_fields or [],
            "isComplete": self.is_complete,
            "status": self.status,
        }
    
    # merge_update is intentionally removed from the model.
    # All merge logic lives in TripStateService (services/trip_state_service.py).
    # Models are pure data containers — no business logic.


class AIResponse(Base):
    """
    Audit log for every Gemini API call.

    Stores the full prompt sent, the raw text response, the parsed JSON,
    latency in milliseconds, and a timestamp. Used for debugging,
    prompt tuning, and observability.

    Attributes:
        id: Unique record identifier
        conversation_id: Which conversation triggered this call
        prompt: The full prompt string sent to Gemini
        raw_response: The raw text Gemini returned
        parsed_json: The parsed and validated JSON (after cleaning)
        latency_ms: Round-trip time to Gemini in milliseconds
        timestamp: When the call was made
    """

    __tablename__ = "ai_responses"

    id = Column(String(50), primary_key=True)
    conversation_id = Column(String(50), ForeignKey("conversations.id"), nullable=False)
    prompt = Column(Text, nullable=False)
    raw_response = Column(Text, nullable=False)
    parsed_json = Column(JSON, nullable=True)
    latency_ms = Column(Float, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationship (no cascade — AI logs are independent audit records)
    conversation = relationship("Conversation")

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "latency_ms": self.latency_ms,
            "timestamp": self.timestamp.isoformat(),
        }
