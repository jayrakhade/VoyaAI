"""
schemas.py

Pydantic schemas for request/response validation.

Purpose:
- Validate incoming API requests
- Ensure API responses have correct structure
- Type hints for all endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, List


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class ChatRequest(BaseModel):
    """Chat message request."""
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID or None for new")
    message: str = Field(..., min_length=1, max_length=2000, description="User message")


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class TripSchema(BaseModel):
    """Trip state in response."""
    source: str = ""
    destination: str = ""
    departure_date: str = ""
    return_date: str = ""
    budget: str = ""
    airline: str = ""
    preferred_time: str = ""
    missing_fields: List[str] = []
    is_complete: bool = False
    status: str = "collecting"
    
    class Config:
        fields = {
            "departure_date": {"alias": "departureDate"},
            "return_date": {"alias": "returnDate"},
            "preferred_time": {"alias": "preferredTime"},
            "missing_fields": {"alias": "missingFields"},
            "is_complete": {"alias": "isComplete"},
        }


class FlightSchema(BaseModel):
    """Flight option in response."""
    airline: str
    flight_no: str
    depart: str
    arrive: str
    duration: str
    stops: str
    price: str


class ChatResponse(BaseModel):
    """Chat response."""
    conversation_id: str = Field(..., description="Conversation ID")
    title: str = Field(..., description="Conversation title")
    assistant_reply: str = Field(..., description="Assistant message")
    trip: TripSchema = Field(..., description="Current trip state")
    status: str = Field("collecting", description="Conversation status")
    flights: List[FlightSchema] = Field([], description="Available flights")
    
    class Config:
        fields = {
            "conversation_id": {"alias": "conversationId"},
            "assistant_reply": {"alias": "assistantReply"},
        }


class ConversationListSchema(BaseModel):
    """Conversation in list response."""
    id: str
    title: str
    status: str
    created_at: str = Field(..., alias="createdAt")
    updated_at: str = Field(..., alias="updatedAt")
    message_count: int = Field(..., alias="messageCount")
    
    class Config:
        allow_population_by_field_name = True


class ConversationsListResponse(BaseModel):
    """Response with list of conversations."""
    conversations: List[ConversationListSchema]
    count: int


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    message: str
    details: Optional[str] = None
