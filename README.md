# VoyaAI — AI-Powered Conversational Flight Booking Assistant

VoyaAI is a conversational AI travel assistant that helps users plan and search for flights through natural language. Powered by Google Gemini 2.5 Flash, it understands travel intent, collects trip details across multiple turns, and presents flight options — all through a chat interface.

---

## Features

- Conversational flight search via natural language
- Multi-turn AI memory — context is preserved across the entire conversation
- Automatic date resolution (understands "tomorrow", "next Friday", "in 3 days")
- Persistent conversation history stored in PostgreSQL
- Conversation sidebar with full session management (create, resume, delete)
- Trip summary panel updated in real time as details are collected
- AI audit log — every Gemini call is stored with prompt, response, and latency
- Retry logic for Gemini API rate limits (429 handling with exponential backoff)

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS v4 |
| Backend | Python, Flask 3, SQLAlchemy 2 |
| AI | Google Gemini 2.5 Flash (`google-genai` SDK) |
| Database | PostgreSQL |
| ORM | SQLAlchemy with Pydantic validation |
| Styling | Tailwind CSS, shadcn/ui components |

---

## Architecture Overview

```
User (Browser)
    │
    ▼
Next.js Frontend (port 3000)
    │  REST API calls
    ▼
Flask Backend (port 5000)
    │
    ├── ConversationService   — CRUD for conversations and messages
    ├── TripStateService      — Merge and persist trip details
    ├── GeminiService         — Calls Gemini API, logs responses
    ├── PromptBuilder         — Builds context-aware prompts
    └── DateResolver          — Converts relative dates to ISO format
    │
    ▼
PostgreSQL Database
    ├── conversations         — Session metadata
    ├── messages              — Full message history
    ├── trip_states           — Current trip details per conversation
    └── ai_responses          — Audit log for every Gemini call
```

**Key design decisions:**
- Gemini does NOT manage state or calculate dates — Python owns both
- One DB session per request, explicit commits only (no auto-commit)
- TripStateService is the single writer to `trip_states` — never overwrite valid fields
- Frontend localStorage is a UI cache only — PostgreSQL is the source of truth

---

## Folder Structure

```
VoyaAI/
├── backend/
│   ├── models/
│   │   └── conversation.py       # SQLAlchemy ORM models
│   ├── services/
│   │   ├── conversation_service.py
│   │   ├── date_resolver.py
│   │   ├── gemini_service.py
│   │   ├── prompt_builder.py
│   │   ├── travel_service.py
│   │   └── trip_state_service.py
│   ├── app.py                    # Flask routes
│   ├── database.py               # DB engine, session, auto-create
│   ├── schemas.py                # Pydantic request/response schemas
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── app/                      # Next.js App Router
│   ├── components/travel/        # Chat, sidebar, summary, nav
│   ├── components/ui/            # Shared UI primitives
│   ├── hooks/                    # React hooks
│   ├── lib/                      # API client, utilities
│   ├── services/                 # chatService (thin wrapper)
│   ├── store/                    # Zustand conversation store
│   ├── types/                    # TypeScript type definitions
│   └── package.json
└── README.md
```

---

## Installation

### Prerequisites

- Python 3.11+
- Node.js 18+ (or use pnpm)
- PostgreSQL 14+
- A Google Gemini API key — [get one here](https://aistudio.google.com/app/apikey)

---

### Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and fill in GEMINI_API_KEY and DATABASE_URL
```

---

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
# or: pnpm install
```

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in the values:

| Variable | Description | Example |
|---|---|---|
| `FLASK_ENV` | Flask environment | `development` |
| `FLASK_DEBUG` | Enable debug mode | `True` |
| `FLASK_PORT` | Backend port | `5000` |
| `FRONTEND_URL` | Allowed CORS origin | `http://localhost:3000` |
| `GEMINI_API_KEY` | Google Gemini API key | `AQ.xxxxx` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/voyaai` |

---

## Database Setup

The backend auto-creates the PostgreSQL database and all tables on first startup — no manual migration needed.

Ensure PostgreSQL is running and the credentials in `DATABASE_URL` are correct. The app will:
1. Connect to the `postgres` maintenance database
2. Create the `voyaai` database if it does not exist
3. Run `CREATE TABLE IF NOT EXISTS` for all models

---

## How to Run

**Start the backend:**
```bash
cd backend
venv\Scripts\activate
python app.py
# → http://localhost:5000
```

**Start the frontend:**
```bash
cd frontend
npm run dev
# → http://localhost:3000
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/chat` | Send a message (creates or continues a conversation) |
| `GET` | `/conversations` | List all conversations |
| `GET` | `/conversations/<id>` | Get conversation with messages and trip state |
| `DELETE` | `/conversations/<id>` | Delete a conversation |
| `GET` | `/health` | Health check |

---

## Current Features (v0.4.0)

- Multi-turn conversational flight search
- AI memory via PostgreSQL (full conversation history injected into every prompt)
- Automatic trip state merging — fields are never overwritten once set
- Natural language date parsing (relative dates resolved server-side)
- Conversation sidebar with session management
- Real-time trip summary panel
- Gemini API audit logging with latency tracking
- Auto-retry on Gemini 429 rate limit errors

---

## Future Roadmap

- [ ] Real flight search API integration (Amadeus / Skyscanner)
- [ ] User authentication and personal conversation history
- [ ] Flight booking and payment flow
- [ ] Email confirmation and itinerary export
- [ ] Multi-city and complex itinerary support
- [ ] Mobile-responsive PWA
- [ ] Deployment to AWS / Vercel

---

## License

MIT License — see [LICENSE](LICENSE) for details.
