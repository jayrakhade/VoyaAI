"""
services/gemini_service.py

GeminiService — the only place that calls the Gemini API.

Responsibilities:
  - Configure and hold the Gemini model (singleton)
  - Build the full prompt via PromptBuilder
  - Call Gemini and parse the JSON response
  - Run Python-side date resolution as a safety net
  - Log every call to the ai_responses table (prompt, response, latency)

Gemini's job (language only):
  - Understand what the user said
  - Extract travel details from natural language
  - Generate a friendly assistant reply
  - Echo back the full trip state (filled + empty fields)

Gemini does NOT:
  - Remember conversation history (we inject it via the prompt)
  - Calculate dates (Python does that in date_resolver.py)
  - Manage state (TripStateService does that)
"""

import os
import json
import re
import time
import uuid
from typing import Any, Dict, Optional

from google import genai
from google.genai import types
from google.genai.errors import ClientError
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from models.conversation import AIResponse
from services.prompt_builder import PromptBuilder
from services.date_resolver import resolve_trip_dates

load_dotenv()

# Retry settings for 429 rate-limit errors
_MAX_RETRIES = 3
_RETRY_BACKOFF = [15, 30, 60]  # seconds to wait before each retry


class GeminiService:
    """Singleton wrapper around the Gemini 2.5 Flash model."""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in .env")

        # New google-genai SDK: client-based API
        self.client = genai.Client(api_key=api_key)
        # gemini-2.0-flash-lite: higher free-tier quota than gemini-2.5-flash
        self.model_name = "gemini-3.1-flash-lite"

    @staticmethod
    def _system_prompt() -> str:
        """
        System-level instructions that persist across all turns.

        Kept intentionally short — detailed per-turn rules are in the
        prompt body built by PromptBuilder. Gemini only needs to know
        its role and output format here.
        """
        return """You are VoyaAI, an AI-powered flight booking assistant.

Your ONLY jobs:
1. Read the CURRENT TRIP STATE provided in the prompt.
2. Extract any new travel information from the user's message.
3. Generate a friendly, concise assistant reply.
4. Return the COMPLETE trip state — echo back every field.
   Fields that already have values MUST be kept exactly as shown.
   Fields the user just provided should be updated.
   Fields still unknown should be empty string.

You do NOT calculate dates. Dates are resolved by the backend.
If the user says "Tomorrow" or "Next Friday", extract that phrase as-is
into the departureDate field. The backend will convert it to YYYY-MM-DD.

Return ONLY valid JSON. No markdown. No code blocks. No extra text."""

    def call(
        self,
        db: Session,
        conv_id: str,
        user_message: str,
        trip_state,
        conversation_history: list,
        today_date: str,
    ) -> Dict[str, Any]:
        """
        Call Gemini with full context and return the parsed response.

        Steps:
          1. Build prompt (PromptBuilder)
          2. Call Gemini, measure latency
          3. Clean and parse JSON
          4. Validate required keys
          5. Resolve dates in Python (safety net)
          6. Log to ai_responses table
          7. Return parsed dict

        Args:
            db: Active SQLAlchemy session (for logging)
            conv_id: Conversation ID (for logging)
            user_message: Current user input
            trip_state: TripState ORM object
            conversation_history: List of Message ORM objects (last 10)
            today_date: ISO date string

        Returns:
            dict: Validated response with assistantReply, trip, status, flights
        """
        prompt = PromptBuilder.build_chat_prompt(
            user_message, trip_state, conversation_history, today_date
        )

        # ── Call Gemini with retry on 429 ─────────────────────────────────────
        start = time.time()
        raw_text = self._call_with_retry(prompt)
        latency_ms = round((time.time() - start) * 1000, 2)
        clean_text = self._strip_fences(raw_text)

        # ── Parse JSON ────────────────────────────────────────────────────────
        try:
            data = json.loads(clean_text)
        except json.JSONDecodeError:
            raise ValueError(
                f"Gemini returned non-JSON (latency={latency_ms}ms): "
                f"{clean_text[:300]}"
            )

        self._validate(data)

        # ── Python-side date resolution (safety net) ──────────────────────────
        # If Gemini returned a relative phrase instead of ISO, resolve it here.
        data["trip"] = resolve_trip_dates(data["trip"], today_date)

        # ── Log to ai_responses ───────────────────────────────────────────────
        self._log(db, conv_id, prompt, raw_text, data, latency_ms)

        return data

    def _call_with_retry(self, prompt: str) -> str:
        """
        Call Gemini and retry up to _MAX_RETRIES times on 429 rate-limit errors.

        On each 429 the error message contains a 'retryDelay' from the API.
        We use that delay if available, otherwise fall back to _RETRY_BACKOFF.

        Args:
            prompt: The full prompt string

        Returns:
            str: Raw response text from Gemini

        Raises:
            Exception: Re-raises after all retries are exhausted
        """
        last_error = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=self._system_prompt(),
                        temperature=0.2,
                    ),
                )
                return response.text.strip()

            except ClientError as e:
                last_error = e
                # Only retry on 429 Resource Exhausted
                if "429" not in str(e) and "RESOURCE_EXHAUSTED" not in str(e):
                    raise

                if attempt >= _MAX_RETRIES:
                    break

                # Use backoff delay
                wait = _RETRY_BACKOFF[attempt]
                print(f"[GeminiService] Rate limited (429). "
                      f"Retry {attempt + 1}/{_MAX_RETRIES} in {wait}s...")
                time.sleep(wait)

        raise last_error

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _strip_fences(text: str) -> str:
        """Remove markdown code fences Gemini sometimes adds despite instructions."""
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)
        return text.strip()

    @staticmethod
    def _validate(data: dict) -> None:
        """Raise ValueError if the response is missing required keys."""
        for key in ("assistantReply", "trip", "flights"):
            if key not in data:
                raise ValueError(f"Gemini response missing top-level key: '{key}'")

        required_trip_keys = (
            "source", "destination", "departureDate",
            "returnDate", "budget", "airline", "preferredTime",
        )
        for key in required_trip_keys:
            if key not in data["trip"]:
                raise ValueError(f"Gemini trip object missing key: '{key}'")

    @staticmethod
    def _log(
        db: Session,
        conv_id: str,
        prompt: str,
        raw_response: str,
        parsed: dict,
        latency_ms: float,
    ) -> None:
        """
        Write an AIResponse audit record.

        Failures here are non-fatal — we log the error but do not
        interrupt the user-facing response.
        """
        try:
            record = AIResponse(
                id=f"ai_{uuid.uuid4().hex[:12]}",
                conversation_id=conv_id,
                prompt=prompt,
                raw_response=raw_response,
                parsed_json=parsed,
                latency_ms=latency_ms,
            )
            db.add(record)
            db.commit()
        except Exception as e:
            print(f"[GeminiService] Failed to log AIResponse: {e}")


# ── Singleton ─────────────────────────────────────────────────────────────────

_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """Return the shared GeminiService instance (lazy init)."""
    global _service
    if _service is None:
        _service = GeminiService()
    return _service
