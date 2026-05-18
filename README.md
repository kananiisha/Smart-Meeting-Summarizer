# Smart Meeting Summarizer 🎙️

An AI-powered meeting summarizer built with Flask and Google Gemini API. Upload audio or paste a transcript — get a structured summary, action items with owners, and key decisions instantly.

## Features
- 🎙️ Audio transcription via **faster-whisper** (tiny model, ~75MB)
- 🤖 Structured AI summarization via **Google Gemini 2.0 Flash**
- ✅ Action items with owner & deadline extraction
- 📋 Key decisions capture
- 🔐 User authentication (Flask-Login + Bcrypt)
- 📊 Meeting history dashboard
- 🌑 Dark UI

## Tech Stack
- **Backend**: Flask, SQLAlchemy, Flask-Login, Flask-Bcrypt
- **AI/ML**: faster-whisper (Whisper tiny), Google Gemini 2.0 Flash
- **Database**: SQLite
- **Frontend**: Jinja2 templates, vanilla CSS/JS

## Setup

### 1. Clone and install dependencies
```bash
cd "Smart Meeting Summarizer"
pip install -r requirements.txt
```

### 2. Configure environment
Copy `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
```

Edit `.env`:
```
SECRET_KEY=your-secret-key-here
GEMINI_API_KEY=your-gemini-api-key-here
DATABASE_URL=sqlite:///meeting_summarizer.db
```

Get your free Gemini API key at: https://aistudio.google.com

### 3. Run the app
```bash
python run.py
```

Visit `http://localhost:5000`

## Project Structure
```
Smart Meeting Summarizer/
├── app/
│   ├── __init__.py       # Flask app factory
│   ├── models.py         # User + MeetingSummary models
│   ├── routes.py         # All routes
│   ├── summarizer.py     # Whisper + Gemini pipeline
│   └── templates/
│       ├── base.html
│       ├── index.html
│       ├── result.html
│       ├── history.html
│       ├── login.html
│       └── register.html
├── static/uploads/       # Uploaded audio files
├── config.py
├── run.py
├── requirements.txt
└── .env
```

## How It Works
1. User uploads audio (.mp3, .wav, etc.) or pastes a text transcript
2. If audio → transcribed locally using faster-whisper tiny model
3. Transcript → sent to Gemini 2.0 Flash API with structured prompt
4. Gemini returns JSON: summary, action_items, key_decisions
5. Results stored in SQLite and displayed in a clean dark UI