# AI Enabled Conversational IVR Modernization Framework

# Indian Railways IVR Backend (FastAPI + Twilio + Conversational AI)


# Importing Dependencies
# ============================================================
from fastapi import FastAPI, Request, Response, Body
from fastapi.middleware.cors import CORSMiddleware
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
import os, re, logging
from dotenv import load_dotenv


#===========================================================
# Load environment variables from .env
load_dotenv() 

# ============================================================
# Configuration (Load from ENV Variables)
# ============================================================

NGROK_URL = os.getenv("NGROK_URL")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")



client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


# ============================================================
# Initialize FastAPI App

app = FastAPI(title="Indian Railways Conversational IVR")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ivr")

# ============================================================
# Regex-based Intent Recognition (Enhanced NLU)
# ============================================================
def detect_intent_regex(text: str) -> str:
    text = text.lower()
    
    if re.search(r"\bcancel|refund\b", text):
        return "cancel_ticket"
    elif re.search(r"\b(book|reserve|ticket|reservation)\b", text):
        return "book_ticket"
    elif re.search(r"\bpnr|status\b", text):
        return "check_pnr"
    elif re.search(r"\bfare|cost|price|how much\b", text):
        return "fare_enquiry"
    elif re.search(r"\btatkal\b", text):
        return "tatkal_info"
    elif re.search(r"\b(agent|operator|representative|customer care)\b", text):
        return "talk_agent"
    elif re.search(r"\bassistance|help|support\b", text):
        return "special_assistance"
    else:
        return "unknown"

# ============================================================
# Context Memory (per-call tracking)
# ============================================================
session_context = {}

# ============================================================
# Contextual Dialogue & Follow-Up Logic
# ============================================================
def next_step(call_id: str, user_text: str):
    """
    Handles follow-up conversation based on previous intent and keeps the call active.
    """
    user_text = user_text.lower()
    context = session_context.get(call_id, {"last_intent": None})
    last_intent = context.get("last_intent")

    # Detect if user wants to end the conversation
    if re.search(r"\b(thank you|thanks|bye|no)\b", user_text):
        resp = VoiceResponse()
        resp.say("Thank you for using Indian Railways helpline. Have a great journey ahead!")
        resp.hangup()
        return Response(content=str(resp), media_type="application/xml")

    # Continue existing booking or enquiry
    if last_intent == "book_ticket":
        if "ac" in user_text:
            response_text = "Booking in A C class selected. Please confirm your travel date."
            context["booking_class"] = "AC"
        elif "sleeper" in user_text:
            response_text = "Booking in Sleeper class selected. Please confirm your travel date."
            context["booking_class"] = "Sleeper"
        elif "tomorrow" in user_text or "today" in user_text or re.search(r"\d{1,2}\s+\w+", user_text):
            # Handles dates like "15 November"
            response_text = f"Booking date {user_text} noted. Your ticket will be processed soon. Would you like to make another enquiry?"
            context["booking_date"] = user_text
        else:
            response_text = "Please specify your class — Sleeper or A C."

    elif last_intent == "check_pnr":
        if user_text.isdigit() and len(user_text) == 10:
            response_text = f"PNR {user_text} is confirmed and the train is running on time. Do you need any further assistance?"
        else:
            response_text = "Please provide a valid ten digit P N R number."

    else:
        response_text = "Sorry, I didn’t understand that. Could you please repeat?"

    # Save context
    session_context[call_id] = context

    # Respond and keep the gather open
    resp = VoiceResponse()
    gather = resp.gather(
        input="speech dtmf",
        action=f"{NGROK_URL}/conversation",
        timeout=5
    )
    gather.say(response_text)

    return Response(content=str(resp), media_type="application/xml")

# ============================================================
# Initial Greeting Endpoint
# ============================================================
@app.post("/voice")
async def voice_start(request: Request):
    """
    Entry point for Twilio call — greets and starts listening for input.
    """
    resp = VoiceResponse()

    gather = resp.gather(
        input="speech dtmf",
        action=f"{NGROK_URL}/conversation",
        timeout=5,
        num_digits=1
    )

    gather.say("Welcome to Indian Railways helpline. "
               "How can I assist you today? "
               "You can say things like book ticket, check P N R, or cancel ticket.")

    # If no input received, repeat greeting
    resp.redirect(f"{NGROK_URL}/voice")

    return Response(content=str(resp), media_type="application/xml")

# ============================================================
# Conversational Endpoint (Main IVR Logic)
# ============================================================
@app.post("/conversation")
async def conversation(request: Request):
    """
    Handles speech or keypad input during an active call.
    """
    form = await request.form()
    call_id = form.get("CallSid")
    user_text = form.get("SpeechResult") or form.get("Digits") or ""

    logger.info(f"Received input from Call {call_id}: {user_text}")

    intent = detect_intent_regex(user_text)
    context = session_context.get(call_id, {})

    # Store last intent
    if intent != "unknown":
        context["last_intent"] = intent
        session_context[call_id] = context

    resp = VoiceResponse()

    if intent == "book_ticket":
        resp.say("You want to book a ticket. Which class would you prefer, Sleeper or A C?")
    elif intent == "check_pnr":
        resp.say("Please tell me your ten digit P N R number.")
    elif intent == "cancel_ticket":
        resp.say("Your ticket cancellation request has been received. Refunds take five to seven days.")
    elif intent == "fare_enquiry":
        resp.say("Train fare enquiry. Please tell me your train number.")
    elif intent == "tatkal_info":
        resp.say("Tatkal booking opens one day in advance at ten A M for A C and eleven A M for non A C classes.")
    elif intent == "talk_agent":
        resp.say("Connecting you to our support agent.")
        resp.dial("+911234567890")
    elif intent == "special_assistance":
        resp.say("Our assistance team will help you shortly.")
    else:
        # If unclear, handle via follow-up
        return next_step(call_id, user_text)

    # Continue listening after speaking
    gather = resp.gather(
        input="speech dtmf",
        action=f"{NGROK_URL}/conversation",
        timeout=5
    )
    gather.say("Is there anything else you’d like help with?")

    return Response(content=str(resp), media_type="application/xml")

# ============================================================
# Start Outbound Call Endpoint
# ============================================================
@app.post("/call/start")
def start_real_call(payload: dict = Body(...)):
    """
    Initiates an outbound call via Twilio API.
    """
    to_number = payload.get("to")
    if not to_number:
        return {"error": "Missing 'to' number"}

    try:
        call = client.calls.create(
            to=to_number,
            from_=TWILIO_PHONE_NUMBER,
            url=f"{NGROK_URL}/voice"   # start from /voice
        )
        logger.info(f"Outbound call started — SID: {call.sid}, To: {to_number}")
        return {
            "status": call.status,
            "sid": call.sid,
            "to": to_number,
            "from": TWILIO_PHONE_NUMBER
        }
    except Exception as e:
        logger.error(f"Twilio call error: {e}")
        return {"error": str(e)}

# ============================================================
#Call End Cleanup

@app.post("/call/end")
async def call_end(request: Request):
    form = await request.form()
    call_id = form.get("CallSid")
    session_context.pop(call_id, None)
    logger.info(f"Call ended and context cleared for {call_id}")
    return Response(status_code=200)
