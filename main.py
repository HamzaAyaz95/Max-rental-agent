from fastapi import FastAPI, Request
from datetime import datetime, timedelta
import json
import requests
import os
from dotenv import load_dotenv


load_dotenv()

app = FastAPI()

CAL_API_KEY = os.getenv("CAL_API_KEY")
CAL_EVENT_TYPE_ID = int(os.getenv("CAL_EVENT_TYPE_ID"))
VAPI_API_KEY = os.getenv("VAPI_API_KEY")
VAPI_PHONE_NUMBER_ID = os.getenv("VAPI_PHONE_NUMBER_ID")

qualified_leads = []

CAL_API_KEY = os.getenv("CAL_API_KEY")
CAL_EVENT_TYPE_ID = int(os.getenv("CAL_EVENT_TYPE_ID"))

def get_first_available_slot():
    url = "https://api.cal.com/v2/slots"
    headers = {
        "Authorization": f"Bearer {CAL_API_KEY}",
        "cal-api-version": "2024-09-04"
    }
    params = {
        "eventTypeId": CAL_EVENT_TYPE_ID,
        "start": datetime.now().strftime("%Y-%m-%d"),
        "end": (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
    }
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    
    print(f"\n🔍 Slots response: {json.dumps(data, indent=2)[:500]}")
    
    # Try different response formats
    slots_data = data.get("data", data)
    if isinstance(slots_data, dict):
        slots = slots_data.get("slots", slots_data)
        for date, times in slots.items():
            if times and isinstance(times, list):
                first = times[0]
                if isinstance(first, dict):
                    return first.get("time") or first.get("start")
                return first
    return None

def auto_book(name: str, email: str):
    try:
        slot = get_first_available_slot()
        if not slot:
            print("❌ No available slots found")
            return None
        
        url = "https://api.cal.com/v2/bookings"
        headers = {
            "Authorization": f"Bearer {CAL_API_KEY}",
            "cal-api-version": "2024-08-13"
        }
        payload = {
            "eventTypeId": CAL_EVENT_TYPE_ID,
            "start": slot,
            "attendee": {
                "name": name,
                "email": email,
                "timeZone": "Europe/Berlin"
            }
        }
        response = requests.post(url, headers=headers, json=payload)
        booking = response.json()
        print(f"\n📅 Auto-booking created for {name} at {slot}")
        print(f"📅 Booking ID: {booking.get('data', {}).get('id')}")
        return booking
    except Exception as e:
        print(f"\n❌ Auto-booking error: {str(e)}")
        return None

@app.get("/")
def root():
    return {"status": "Max Rental Agent is running"}

@app.post("/webhook")
async def vapi_webhook(request: Request):
    data = await request.json()
    
    print("\n--- Incoming Vapi Webhook ---")
    
    message_type = data.get("message", {}).get("type", "")
    
    if message_type == "end-of-call-report":
        call_data = data.get("message", {})
        
        summary = call_data.get("analysis", {}).get("summary", "")
        success = call_data.get("analysis", {}).get("successEvaluation", "")
        qualified = success == "true"
        
        lead = {
            "timestamp": datetime.now().isoformat(),
            "call_id": call_data.get("call", {}).get("id", ""),
            "transcript": call_data.get("transcript", ""),
            "summary": summary,
            "qualified": qualified,
            "duration_seconds": call_data.get("durationSeconds", 0),
            "booking": None
        }
        
        if qualified:
            print(f"\n✅ Caller qualified! Auto-booking viewing...")
            booking = auto_book(
                name="Apartment Applicant",
                email="applicant@example.com"
            )
            if booking:
                lead["booking"] = booking
                print(f"✅ Viewing booked automatically!")
        else:
            print(f"\n❌ Caller did not qualify")
        
        qualified_leads.append(lead)
        print(f"✅ Lead saved: {lead['call_id']}")
    
    return {"status": "ok"}

@app.get("/leads")
def get_leads():
    return {"total": len(qualified_leads), "leads": qualified_leads}

@app.get("/slots")
def get_available_slots():
    slot = get_first_available_slot()
    return {"next_available_slot": slot}

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
        return response.json()
    except Exception as e:
        return {"error": str(e)}

@app.post("/outbound-call")
def make_outbound_call(phone_number: str, applicant_name: str):
    try:
        url = "https://api.vapi.ai/call"
        headers = {
            "Authorization": f"Bearer {VAPI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "assistant": {
                "model": {
                    "provider": "openai",
                    "model": "gpt-4.1-mini",
                    "messages": [
                        {
                            "role": "system",
                            "content": f"""You are Max, a friendly male AI rental assistant for Urban Rentals Berlin.
You are calling {applicant_name} because they expressed interest in our apartment.

APARTMENT DETAILS:
- 3 rooms, 85 sqm, Prenzlauer Berg Berlin
- Cold rent: €1,450/month, Warm rent: €1,650/month
- Available August 1st 2026
- Pets allowed, no smoking

YOUR JOB:
1. Introduce yourself and explain why you're calling
2. Ask if this is a good time to talk
3. Ask qualification questions ONE AT A TIME:
   - How many people will be living in the apartment?
   - What is your monthly net income?
   - When would you like to move in?
   - Do you have any pets?
4. If they qualify (income €4350+, move-in after Aug 1), offer to book a viewing
5. If voicemail is detected, leave a brief friendly message and hang up
6. Keep responses short and natural — this is a phone call"""
                        }
                    ]
                },
                "voice": {
                    "provider": "vapi",
                    "voiceId": "Elliot"
                },
                "firstMessage": f"Hi {applicant_name}, this is Max calling from Urban Rentals Berlin. I saw you expressed interest in our apartment in Prenzlauer Berg. Is this a good time to chat for a few minutes?"
            },
            "phoneNumberId": VAPI_PHONE_NUMBER_ID,
            "customer": {
                "number": phone_number
            }
        }
        response = requests.post(url, headers=headers, json=payload)
        print(f"\n📞 Outbound call initiated: {response.json()}")
        return response.json()
    except Exception as e:
        print(f"\n❌ Outbound call error: {str(e)}")
        return {"error": str(e)}

    