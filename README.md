# InsightFlow 🧠⚡

**An AI Competitive Intelligence & Knowledge Evolution Engine that remembers how strategic understanding evolves over time.**

> "Companies don't suffer from lack of information. They suffer from loss of organizational memory. InsightFlow preserves not just facts, but the evolution of reasoning itself."

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- A Groq API key (set in `backend/.env`)

### 1. Backend Setup
```bash
cd backend
pip install -r requirements.txt
python run.py
# Runs on http://localhost:8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:3000
```

### 3. Open in Browser
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

## 🏗️ Architecture

```
Frontend (Next.js + Tailwind CSS)
        │
        ▼
FastAPI Backend (Python)
        │
        ├── Groq LLM (Intelligence Extraction, Q&A, Contradiction Detection)
        │
        └── SQLite Database (Hindsight Memory Storage)
```

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📄 **Document Upload** | Upload PDF, TXT, MD files for AI intelligence extraction |
| 🌐 **URL Ingestion** | Paste any URL (Reuters, blogs, SEC) for instant analysis |
| 💾 **Hindsight Memory** | Every insight is stored with evidence, assumptions, and confidence |
| 📊 **Knowledge Timeline** | Watch how strategic understanding evolves over time |
| ⚠️ **Contradiction Detection** | AI spots when new evidence contradicts old assumptions |
| 💡 **Strategic Q&A** | Ask questions and get evidence-backed, explainable answers |
| 🔍 **Evidence Explorer** | Browse all collected intelligence, memories, and contradictions |

## 🔐 Security

- API key stored in `backend/.env` (never exposed to frontend)
- `.gitignore` prevents committing secrets
- Workspace isolation for data separation

## 🧪 Example Questions

- "How has Tesla evolved?"
- "What assumptions changed?"
- "What evidence supports this?"
- "What trends are emerging?"
- "What did we get wrong?"
- "Why did our strategy shift?"
