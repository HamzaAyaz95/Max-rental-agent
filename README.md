# Max Rental Agent 🏠

A voice AI agent that automatically handles apartment rental inquiries for property owners in Germany.

Max answers inbound calls, qualifies tenants, and books viewings automatically. No human needed until the viewing itself.

## Demo

## Demo

🎥 [Watch Demo Video](https://www.loom.com/share/57a099d601644634891c177eebd7dad2)

📞 Live agent available — contact me for access

## What Max Does

1. Answers calls and explains the apartment
2. Qualifies callers (income, household size, move-in date, pets)
3. Auto-books a Cal.com viewing if they qualify
4. Rejects unqualified callers politely
5. Sends all data to a FastAPI webhook for logging

## Architecture

Caller → Vapi.ai (STT + LLM + TTS) → FastAPI Webhook → Cal.com Booking

## Tech Stack

| Component | Technology |
|-----------|------------|
| Voice Layer | Vapi.ai |
| LLM | GPT-4.1 Mini |
| Speech Recognition | Deepgram |
| Backend | FastAPI (Python) |
| Booking | Cal.com API v2 |
| Tunnel | ngrok (dev) |

## Project Structure

max-rental-agent/
├── main.py              # FastAPI backend + webhook handler
├── apartment.json       # Apartment knowledge base
├── golden_dataset.csv   # 15 labeled test cases for eval
├── eval.py              # Evaluation script (100% pass rate)
└── .gitignore

## How It Works

### 1. Voice Agent (Vapi.ai)
Max is configured with a detailed system prompt containing apartment information. When someone calls, Max answers, explains the apartment, and proactively qualifies the caller.

### 2. Qualification Logic
Max asks four questions one at a time:
- Household size
- Monthly net income (minimum €4,350 required)
- Move-in date (must be after August 1st 2026)
- Pets

### 3. Auto-Booking
When a caller qualifies, the Vapi webhook triggers `auto_book()` which:
- Fetches the first available Cal.com slot
- Creates a booking via Cal.com API v2
- Logs the lead with booking confirmation

### 4. Golden Dataset & Eval
15 labeled test cases covering apartment Q&A, qualification scenarios, and edge cases. Eval script scores agent response quality.

```bash
python eval.py
# Score: 100.0%
```

## Setup

```bash
# Clone the repo
git clone https://github.com/HamzaAyaz95/Max-rental-agent.git
cd Max-rental-agent

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install fastapi uvicorn python-dotenv requests

# Create .env file
CAL_API_KEY=your_cal_api_key
CAL_EVENT_TYPE_ID=your_event_type_id

# Run the server
uvicorn main:app --reload
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/webhook` | POST | Vapi webhook receiver |
| `/leads` | GET | View all saved leads |
| `/slots` | GET | Get next available Cal.com slot |
| `/book` | POST | Manual booking endpoint |

## Latency

Average end-to-end latency: **~1,220ms**
- Transcriber (Deepgram): 100ms
- LLM (GPT-4.1 Mini): 770ms  
- Voice (Vapi TTS): 250ms

## What I'd Build Next

- Connect eval script to live call transcripts for automated regression testing
- Add retry logic for unanswered calls (scheduled tasks via Airflow)
- Extract caller name and email from transcript for personalized bookings
- German language support
- Deploy to Railway for persistent hosting

## Built By

Hamza Ayaz — Data Engineer & AI Builder
