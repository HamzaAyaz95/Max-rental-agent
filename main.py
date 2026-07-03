from fastapi import FastAPI, Request
from datetime import datetime
import json
import requests
import os

app = FastAPI()

# Store qualified leads in memory
qualified_leads = []

CAL_API_KEY = "cal_live_71beca80c2abe36f358e9fc8efbd5b6a"
CAL_EVENT_TYPE_ID = 6202891  # we'll get this next

@app.get("/")
def root():
    return {"status": "Max Rental Agent is running"}

@app.post("/webhook")
async def vapi_webhook(request: Request):
    data = await request.json()
    
    print("\n--- Incoming Vapi Webhook ---")
    print(json.dumps(data, indent=2))
    
    message_type = data.get("message", {}).get("type", "")
    
    if message_type == "end-of-call-report":
        call_data = data.get("message", {})
        
        summary = call_data.get("analysis", {}).get("summary", "")
        success = call_data.get("analysis", {}).get("successEvaluation", "")
        
        lead = {
            "timestamp": datetime.now().isoformat(),
            "call_id": call_data.get("call", {}).get("id", ""),
            "transcript": call_data.get("transcript", ""),
            "summary": summary,
            "qualified": success == "true",
            "duration_seconds": call_data.get("durationSeconds", 0),
        }
        
        qualified_leads.append(lead)
        print(f"\n✅ Lead saved: {lead['call_id']}")
        print(f"   Qualified: {lead['qualified']}")
        print(f"   Summary: {summary[:100]}...")
    
    return {"status": "ok"}

@app.get("/leads")
def get_leads():
    return {"total": len(qualified_leads), "leads": qualified_leads}

@app.get("/slots")
def get_available_slots():
    url = f"https://api.cal.com/v2/slots"
    headers = {
        "Authorization": f"Bearer {CAL_API_KEY}",
        "cal-api-version": "2024-09-04"
    }
    params = {
        "eventTypeId": CAL_EVENT_TYPE_ID,
        "start": datetime.now().strftime("%Y-%m-%d"),
        "end": "2026-07-31",
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json()

@app.post("/book")
def book_slot(name: str, email: str, start_time: str):
    try:
        url = "https://api.cal.com/v2/bookings"
        headers = {
            "Authorization": f"Bearer {CAL_API_KEY}",
            "cal-api-version": "2024-08-13"
        }
        payload = {
            "eventTypeId": CAL_EVENT_TYPE_ID,
            "start": start_time,
            "attendee": {
                "name": name,
                "email": email,
                "timeZone": "Europe/Berlin"
            }
        }
        response = requests.post(url, headers=headers, json=payload)
        print(f"\n📅 Booking status: {response.status_code}")
        print(f"📅 Booking response: {response.text}")
        return response.json()
    except Exception as e:
        print(f"\n❌ Booking error: {str(e)}")
        return {"error": str(e)}