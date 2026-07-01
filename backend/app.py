"""
app.py

VoyaAI Flask application.

Routes:
  POST   /chat                    — Send a message (creates or continues a conversation)
  GET    /conversations           — List all conversations
  GET    /conversations/<id>      — Get one conversation with messages + trip
  DELETE /conversations/<id>      — Delete a conversation
  GET    /health                  — Health check
"""

import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from database import init_db, DBSession
from services.travel_service import process_chat_message
from services.conversation_service import ConversationService

load_dotenv()

app = Flask(__name__)

CORS(app, resources={
    r"/*": {
        "origins": [os.getenv("FRONTEND_URL", "http://localhost:3000")],
        "methods": ["GET", "POST", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Create tables on startup
with app.app_context():
    init_db()


# ── /chat ────────────────────────────────────────────────────────────────────

@app.route("/chat", methods=["POST"])
def chat():
    """
    Process a user message.

    Request:  { "conversationId": str|null, "message": str }
    Response: { "conversationId", "title", "assistantReply", "trip", "status", "flights" }
    """
    data = request.get_json()
    if not data or not data.get("message", "").strip():
        return jsonify({"error": "Bad Request", "message": "Missing 'message'"}), 400

    try:
        result = process_chat_message(
            user_message=data["message"].strip(),
            conversation_id=data.get("conversationId")
        )
        return jsonify(result), 200
    except Exception as e:
        print(f"[/chat] Error: {e}")
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500


# ── /conversations ───────────────────────────────────────────────────────────

@app.route("/conversations", methods=["GET"])
def list_conversations():
    """Return all conversations sorted by most recent first."""
    try:
        with DBSession() as db:
            convs = ConversationService.get_all_conversations(db)
            return jsonify({
                "conversations": [c.to_dict() for c in convs],
                "count": len(convs)
            }), 200
    except Exception as e:
        print(f"[/conversations] Error: {e}")
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500


@app.route("/conversations/<conv_id>", methods=["GET"])
def get_conversation(conv_id: str):
    """Return a single conversation with its messages and trip state."""
    try:
        with DBSession() as db:
            conv = ConversationService.get_conversation(db, conv_id)
            if not conv:
                return jsonify({"error": "Not Found", "message": "Conversation not found"}), 404

            trip = ConversationService.get_trip_state(db, conv_id)
            messages = ConversationService.get_messages(db, conv_id, limit=100)

            return jsonify({
                "conversation": conv.to_dict(),
                "messages": [m.to_dict() for m in messages],
                "trip": trip.to_dict() if trip else {}
            }), 200
    except Exception as e:
        print(f"[/conversations/{conv_id}] Error: {e}")
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500


@app.route("/conversations/<conv_id>", methods=["DELETE"])
def delete_conversation(conv_id: str):
    """Delete a conversation and all its data."""
    try:
        with DBSession() as db:
            deleted = ConversationService.delete_conversation(db, conv_id)
            if not deleted:
                return jsonify({"error": "Not Found", "message": "Conversation not found"}), 404
            return jsonify({"success": True}), 200
    except Exception as e:
        print(f"[DELETE /conversations/{conv_id}] Error: {e}")
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500


# ── /health ──────────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "service": "VoyaAI Backend"}), 200


# ── Error handlers ───────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not Found"}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method Not Allowed"}), 405


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_ENV") == "development"
    sys.stdout.buffer.write(f"VoyaAI Backend -> http://localhost:{port}\n".encode("utf-8"))
    sys.stdout.flush()

    # Exclude site-packages from the reloader so leftover google.generativeai
    # rename artifacts don't trigger infinite reloads in debug mode.
    extra_exclude = []
    for path in sys.path:
        if "site-packages" in path:
            extra_exclude.append(path)

    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug,
        exclude_patterns=extra_exclude,
    )
