# AI Enabled Conversational IVR Modernization Framework

# Indian Railways IVR Backend (FastAPI + Twilio + Conversational AI)

from fastapi import FastAPI, Request, Response, Body
from fastapi.middleware.cors import CORSMiddleware
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
import os
import re
import logging
from dotenv import load_dotenv
from typing import Optional
import google.generativeai as genai

# Load environment variables from .env (local dev). On Render, set env vars in dashboard.
load_dotenv()

# ===========================
# Configuration (ENV)
# ===========================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
BASE_WEBHOOK_URL = os.getenv("BASE_WEBHOOK_URL", "").rstrip("/")  # ⚠️ Set this to your Render URL (no trailing slash)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
SUPPORT_PHONE_NUMBER = os.getenv("SUPPORT_PHONE_NUMBER", "")  # optional agent number for dialing

# Twilio client only if credentials present
client: Optional[Client] = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    except Exception as e:
        client = None

# ===========================
# Gemini API Configuration
# ===========================
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        logger.error(f"Failed to configure Gemini API: {e}")

def detect_intent_gemini(text: str) -> str:
    """
    Detects intent using Gemini API.
    """
    if not GEMINI_API_KEY:
        return "unknown"
    try:
        model = genai.GenerativeModel('gemini-pro')
        prompt = f"""
        You are an intent detection system for an Indian Railways IVR.
        Your task is to identify the user's intent from their speech.
        The user said: "{text}"

        Return one of the following intents:
        - book_ticket
        - check_pnr
        - cancel_ticket
        - fare_enquiry
        - tatkal_info
        - talk_agent
        - special_assistance
        - train_live_status
        - platform_locator
        - unknown

        Return only the intent name.
        """
        response = model.generate_content(prompt)
        intent = response.text.strip()
        # Basic validation to ensure the model returns a valid intent
        valid_intents = [
            "book_ticket", "check_pnr", "cancel_ticket", "fare_enquiry",
            "tatkal_info", "talk_agent", "special_assistance",
            "train_live_status", "platform_locator", "unknown"
        ]
        if intent in valid_intents:
            return intent
        else:
            logger.warning(f"Gemini returned an invalid intent: {intent}")
            return "unknown"
    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}")
        return "unknown"

# ===========================
# FastAPI app + CORS
# ===========================
app = FastAPI(title="Indian Railways Conversational IVR")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===========================
# Logging
# ===========================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ivr")

# ===========================
# Session context (per-call)
# Simple in-memory dict; replace with redis/db for production scale.
# ===========================
session_context = {}

# ===========================
# Intent detection 
# Handles both DTMF digits and free-form speech.
# ===========================
def map_digits_to_intent(digits: str) -> str:
    mapping = {
        "1": "book_ticket",
        "2": "check_pnr",
        "3": "cancel_ticket",
        "4": "fare_enquiry",
        "5": "tatkal_info",
        "6": "talk_agent",
        "7": "special_assistance",
        "8": "train_live_status",
        "9": "platform_locator",
    }
    return mapping.get(digits, "unknown")

def detect_intent(text: str) -> str:
    """
    Unified intent detection for speech text (lowercased).
    Returns one of the known intents or 'unknown'.
    """
    if text is None:
        return "unknown"
    text = text.lower().strip()

    # If the user pressed a digit-like input, let the digit-mapper handle it
    if re.fullmatch(r"\d+", text):
        return map_digits_to_intent(text)

    # Try Gemini API first
    intent = detect_intent_gemini(text)
    if intent != "unknown":
        return intent

    # Fallback to regex if Gemini fails or is not configured
    if re.search(r"\b(cancel|refund)\b", text):
        return "cancel_ticket"
    if re.search(r"\b(book|reserve|ticket|reservation)\b", text):
        return "book_ticket"
    if re.search(r"\b(pnr|status)\b", text):
        return "check_pnr"
    if re.search(r"\b(fare|cost|price|how much)\b", text):
        return "fare_enquiry"
    if re.search(r"\btatkal\b", text):
        return "tatkal_info"
    if re.search(r"\b(agent|operator|representative|customer care)\b", text):
        return "talk_agent"
    if re.search(r"\b(assistance|help|support)\b", text):
        return "special_assistance"
    if re.search(r"\b(live status|running status|where is train|running)\b", text):
        return "train_live_status"
    if re.search(r"\b(platform|which platform|where platform)\b", text):
        return "platform_locator"

    return "unknown"

# ===========================
# If BASE_WEBHOOK_URL is missing, action will be blank (Twilio expects a full URL in production).
# ===========================
def webhook(path: str) -> str:
    if BASE_WEBHOOK_URL:
        return f"{BASE_WEBHOOK_URL}{path}"
    # If not set, return path only — useful for local tests with TestClient (no external Twilio)
    return path

# ===========================
# Conversation follow-up handler (keeps call active)
# ===========================
def next_step(call_id: str, user_text: str):
    user_text = (user_text or "").lower()
    context = session_context.get(call_id, {"last_intent": None})
    last_intent = context.get("last_intent")

    # End conversation if user says goodbye / thanks / no
    if re.search(r"\b(thank you|thanks|bye|no|goodbye)\b", user_text):
        resp = VoiceResponse()
        resp.say("Thank you for using Indian Railways helpline. Have a great journey ahead!")
        resp.hangup()
        # Clear context
        session_context.pop(call_id, None)
        return Response(content=str(resp), media_type="application/xml")

    # Follow-ups per last intent
    if last_intent == "book_ticket":
        if "ac" in user_text or user_text == "1" or user_text == "ac":
            context["booking_class"] = "AC"
            response_text = "A C class selected. Please confirm your travel date."
        elif "sleeper" in user_text or user_text == "2" or user_text == "sleeper":
            context["booking_class"] = "Sleeper"
            response_text = "Sleeper class selected. Please confirm your travel date."
        elif "tomorrow" in user_text or "today" in user_text or re.search(r"\d{1,2}\s+\w+", user_text):
            context["booking_date"] = user_text
            response_text = f"Booking date {user_text} noted. Your ticket will be processed soon. Would you like anything else?"
        else:
            response_text = "Please specify your class — Sleeper or AC."

    elif last_intent == "check_pnr":
        if user_text.isdigit() and len(user_text) == 10:
            response_text = f"PNR {user_text} is confirmed. The train is running on time. Need further help?"
            # could attach more PNR metadata here
        else:
            response_text = "Please provide a valid ten digit P N R number."

    elif last_intent == "train_live_status":
        # expected: train number in user_text
        response_text = f"Fetching live running status for train {user_text}. The train is currently reported on time."

    elif last_intent == "platform_locator":
        response_text = f"Platform information for train {user_text}: It is expected to arrive at platform number 5."

    else:
        response_text = "Sorry, I didn’t understand that. Could you please repeat?"

    # Save updated context
    session_context[call_id] = context

    # Build TwiML response and keep gather open for more input
    resp = VoiceResponse()
    gather = resp.gather(
        input="speech dtmf",
        action=webhook("/conversation"),
        timeout=5
    )
    gather.say(response_text)
    return Response(content=str(resp), media_type="application/xml")

# ===========================
# /voice — initial greeting endpoint
# ===========================
@app.post("/voice")
async def voice_start(request: Request):
    """
    Entry point for Twilio call — greets and starts listening for input.
    """
    resp = VoiceResponse()
    gather = resp.gather(
        input="speech dtmf",
        num_digits=1,
        timeout=5,
        action=webhook("/conversation")
    )

    gather.say(
        "Welcome to Indian Railways helpline. "
        "You can speak naturally or press a number. "
        "For booking a ticket press 1. "
        "To check P N R status press 2. "
        "To cancel your ticket press 3. "
        "For fare enquiry press 4. "
        "For Tatkal information press 5. "
        "To talk to an agent press 6. "
        "For special assistance press 7. "
        "For live train running status press 8. "
        "For platform locator press 9."
    )

    # If no input received, repeat greeting (redirect)
    resp.redirect(webhook("/voice"))
    return Response(content=str(resp), media_type="application/xml")

# ===========================
# /conversation — main IVR logic
# ===========================
@app.post("/conversation")
async def conversation(request: Request):
    """
    Handles speech or keypad (DTMF) input during an active call.
    """
    form = await request.form()
    call_id = form.get("CallSid") or form.get("CallSid", "")
    speech_result = form.get("SpeechResult") or ""
    digits = form.get("Digits") or ""
    user_text = speech_result or digits or ""

    logger.info(f"Received input from Call {call_id}: {user_text}")

    # Detect intent (unified). digits map to intents automatically.
    intent = detect_intent(user_text)
    context = session_context.get(call_id, {})

    # Store last intent if known
    if intent and intent != "unknown":
        context["last_intent"] = intent
        session_context[call_id] = context

    resp = VoiceResponse()

    # Intent handling
    if intent == "book_ticket":
        resp.say("You want to book a ticket. Which class would you prefer, Sleeper or AC? Press 1 for AC and 2 for Sleeper, or say your choice.")

    elif intent == "check_pnr":
        resp.say("Please tell me your ten digit P N R number.")

    elif intent == "cancel_ticket":
        resp.say("Your ticket cancellation request has been received. Refunds take five to seven days.")

    elif intent == "fare_enquiry":
        resp.say("Train fare enquiry. Please tell me your train number.")

    elif intent == "tatkal_info":
        resp.say("Tatkal booking opens one day in advance: 10 AM for AC and 11 AM for non-AC classes.")

    elif intent == "talk_agent":
        resp.say("Connecting you to a support agent.")
        # Dial support number if available, otherwise a fallback
        agent_number = SUPPORT_PHONE_NUMBER or "+911234567890"
        resp.dial(agent_number)
        # Return immediately because Twilio will connect the call
        return Response(content=str(resp), media_type="application/xml")

    elif intent == "special_assistance":
        resp.say("Our special assistance team will help you shortly. Please hold.")

    elif intent == "train_live_status":
        resp.say("Please tell me your train number to check live running status.")

    elif intent == "platform_locator":
        resp.say("Please tell me your train number to locate the platform.")

    else:
        # Unknown intent -> forward to follow-up handler which may ask clarifying question
        return next_step(call_id, user_text)

    # Keep listening after speaking
    gather = resp.gather(
        input="speech dtmf",
        action=webhook("/conversation"),
        timeout=5
    )
    gather.say("Is there anything else you’d like help with?")

    return Response(content=str(resp), media_type="application/xml")

# ===========================
# /call/start — start outbound call via Twilio REST API
# ===========================
@app.post("/call/start")
def start_real_call(payload: dict = Body(...)):
    """
    Initiates an outbound call via Twilio API to `to` number.
    Requires TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER in environment.
    """
    to_number = payload.get("to")
    if not to_number:
        return {"error": "Missing 'to' number"}

    if client is None or not TWILIO_PHONE_NUMBER:
        logger.error("Twilio client not configured. Outbound calls are disabled.")
        return {"error": "Twilio not configured on server"}

    # Use BASE_WEBHOOK_URL for call callback
    if not BASE_WEBHOOK_URL:
        logger.error("BASE_WEBHOOK_URL not configured; outbound call will fail without a public URL.")
        return {"error": "BASE_WEBHOOK_URL not configured"}

    try:
        call = client.calls.create(
            to=to_number,
            from_=TWILIO_PHONE_NUMBER,
            url=f"{BASE_WEBHOOK_URL}/voice"
        )
        logger.info(f"Outbound call started — SID: {call.sid}, To: {to_number}")
        return {"status": call.status, "sid": call.sid, "to": to_number}
    except Exception as e:
        logger.error(f"Twilio call error: {e}")
        return {"error": str(e)}

# ===========================
# /call/end — cleanup after call ends 
# ===========================
@app.post("/call/end")
async def call_end(request: Request):
    form = await request.form()
    call_id = form.get("CallSid")
    session_context.pop(call_id, None)
    logger.info(f"Call ended and context cleared for {call_id}")
    return Response(status_code=200)
