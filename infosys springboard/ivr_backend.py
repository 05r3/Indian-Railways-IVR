#MODULE 3

# Indian Railways IVR Backend (FastAPI + Twilio + Conversational AI)


from fastapi import FastAPI, Request, Response, Body
from fastapi.middleware.cors import CORSMiddleware
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client
import os

# Configuration


NGROK_URL = "" 
TWILIO_ACCOUNT_SID = ""
TWILIO_AUTH_TOKEN = ""
TWILIO_PHONE_NUMBER = ""

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

app = FastAPI(title="Indian Railways Conversational IVR", version="3.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#Intent Keyword Mapping 

INTENT_KEYWORDS = {
    "book_ticket": ["book", "ticket", "reservation", "train booking", "reserve"],
    "check_pnr": ["pnr", "status", "train status", "check"],
    "cancel_ticket": ["cancel", "cancellation", "refund"],
    "fare_enquiry": ["fare", "price", "cost", "how much"],
    "tatkal_info": ["tatkal"],
    "talk_agent": ["agent", "representative", "customer care", "help", "operator"],
    "special_assistance": ["help", "assistance", "support"]
}

def recognize_intent(speech_text: str) -> str:
    """Keyword-based intent recognizer with fallback."""
    if not speech_text:
        return "unknown"
    speech_text = speech_text.lower()

    for intent, keywords in INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in speech_text:
                return intent
    return "unknown"



#Context Memory

session_context = {}

# Contextual Dialogue & Follow-Up


def next_step(call_id: str, user_text: str):
    """Handles follow-up user messages contextually"""
    user_text = user_text.lower()
    context = session_context.get(call_id, {"last_intent": None})
    last_intent = context.get("last_intent")

    if last_intent == "book_ticket":
        if "ac" in user_text:
            response_text = "Booking in A C class selected. Please confirm your travel date."
            context["booking_class"] = "AC"
        elif "sleeper" in user_text:
            response_text = "Booking in Sleeper class selected. Please confirm your travel date."
            context["booking_class"] = "Sleeper"
        elif "tomorrow" in user_text or "today" in user_text:
            response_text = f"Booking date {user_text} noted. Your ticket will be processed soon. Thank you."
            context["booking_date"] = user_text
        else:
            response_text = "Please specify your class — Sleeper or A C."

    elif last_intent == "check_pnr":
        if user_text.isdigit() and len(user_text) == 10:
            response_text = f"PNR {user_text} is confirmed and the train is running on time."
        else:
            response_text = "Please provide a valid ten digit P N R number."

    else:
        response_text = "Sorry, I didn’t understand that. Could you please repeat?"

    session_context[call_id] = context
    resp = VoiceResponse()
    resp.say(response_text)
    return Response(content=str(resp), media_type="application/xml")



# Conversational Endpoint


@app.post("/conversation")
async def conversation(request: Request):
    """Handles both speech-based and contextual conversation"""
    form = await request.form()
    call_id = form.get("CallSid")
    user_text = form.get("SpeechResult", "") or form.get("Digits", "")

    print(f"Received speech from Call {call_id}: {user_text}")

    intent = recognize_intent(user_text)
    context = session_context.get(call_id, {})

    # Store last intent
    if intent != "unknown":
        context["last_intent"] = intent
        session_context[call_id] = context

    resp = VoiceResponse()

    #  Mapping intents to backend responses 
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
        #  Added fallback
        return next_step(call_id, user_text)

    return Response(content=str(resp), media_type="application/xml")

# Launch IVR Session/Start a call


@app.post("/call/start")
def start_real_call(payload: dict = Body(...)):
    """Initiates outbound call via Twilio"""
    to_number = payload.get("to")
    if not to_number:
        return {"error": "Missing 'to' number"}

    try:
        call = client.calls.create(
            to=to_number,
            from_=TWILIO_PHONE_NUMBER,
            url=f"{NGROK_URL}/conversation"
        )
        print(f" Outbound call started — SID: {call.sid}, To: {to_number}")
        return {
            "status": call.status,
            "sid": call.sid,
            "to": to_number,
            "from": TWILIO_PHONE_NUMBER
        }
    except Exception as e:
        print(" Twilio call error:", e)
        return {"error": str(e)}

