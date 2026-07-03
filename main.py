from fastapi import FastAPI, Request
from datetime import datetime
import json

app = FastAPI()

# Store qualified leads in memory for now
qualified_leads = []

@app.get("/")
def root():
    return {"status": "Max Rental Agent is running"}

@app.post("/webhook")
async def vapi_webhook(request: Request):
    data = await request.json()
    
    # Print incoming data so we can see what Vapi sends
    print("\n--- Incoming Vapi Webhook ---")
    print(json.dumps(data, indent=2))
    
    # Get the message type
    message_type = data.get("message", {}).get("type", "")
    
    # When a call ends, extract and save the lead info
    if message_type == "end-of-call-report":
        call_data = data.get("message", {})
        
        lead = {
            "timestamp": datetime.now().isoformat(),
            "call_id": call_data.get("call", {}).get("id", ""),
            "transcript": call_data.get("transcript", ""),
            "summary": call_data.get("summary", ""),
            "duration_seconds": call_data.get("durationSeconds", 0),
        }
        
        qualified_leads.append(lead)
        print(f"\n✅ Lead saved: {lead['call_id']}")
    
    return {"status": "ok"}

@app.get("/leads")
def get_leads():
    return {"total": len(qualified_leads), "leads": qualified_leads}