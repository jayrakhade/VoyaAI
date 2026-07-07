# ✈️ VoyaAI – AI-Powered Conversational Travel Assistant

VoyaAI is an AI-powered conversational travel assistant that helps users plan their trips through natural language. It understands travel preferences, collects trip details, maintains conversation history, and is designed to support future flight search and booking capabilities.

> **Project Status:** 🚧 Active Development

---

## 🚀 Features

- Natural language conversation using Google Gemini
- Multi-turn chat with conversation memory
- Automatic understanding of relative travel dates
- Real-time trip information collection
- Persistent conversation history using PostgreSQL
- Modular backend architecture for future integrations

---

## 🛠️ Tech Stack

### Frontend
- Next.js
- React
- TypeScript
- Tailwind CSS

### Backend
- Python
- Flask
- SQLAlchemy

### AI
- Google Gemini API

### Database
- PostgreSQL

---

## 🏗️ Architecture

```text
User
   │
   ▼
Next.js Frontend
   │
 REST API
   ▼
Flask Backend
   │
   ├── Google Gemini API
   ├── PostgreSQL
   └── Trip Management
```

---

## 📂 Project Structure

```
VoyaAI/
├── frontend/
├── backend/
├── README.md
└── .env.example
```

---

## ⚙️ Getting Started

### Clone the repository

```bash
git clone https://github.com/jayrakhade/voyaai.git
```

### Backend

```bash
cd backend
pip install -r requirements.txt
python app.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 📸 Screenshots

> Screenshots will be added as the project evolves.

---

## 🎯 Roadmap

- ✅ Conversational AI interface
- ✅ Conversation history
- ✅ Trip information collection
- 🔄 Flight search integration
- 🔄 Flight booking workflow
- 🔄 User authentication
- 🔄 Cloud deployment

---

## 🤝 Contributing

Contributions, suggestions, and feedback are always welcome.

---

## 📄 License

MIT License
