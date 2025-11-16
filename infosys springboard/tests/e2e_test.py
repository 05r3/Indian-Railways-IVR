import pytest
from fastapi.testclient import TestClient
from ivr_backend import app, session_context

client = TestClient(app)

# END-TO-END BOOKING FLOW

def test_e2e_full_booking_flow():
    call_id = "e2e001"

    # Step 1: User dials in
    r1 = client.post("/voice")
    assert r1.status_code == 200
    assert "Welcome" in r1.text

    # Step 2: Says "book ticket"
    r2 = client.post("/conversation", data={"CallSid": call_id, "SpeechResult": "book ticket"})
    assert "book a ticket" in r2.text.lower()

    # Step 3: Says "AC"
    r3 = client.post("/conversation", data={"CallSid": call_id, "SpeechResult": "AC"})
    assert "A C class" in r3.text

    # Step 4: Says "tomorrow"
    r4 = client.post("/conversation", data={"CallSid": call_id, "SpeechResult": "tomorrow"})
    assert "Booking date" in r4.text

    # Step 5: Says "thank you"
    r5 = client.post("/conversation", data={"CallSid": call_id, "SpeechResult": "thank you"})
    assert "Thank you" in r5.text
    assert "<Hangup" in r5.text

    # Step 6: End call
    r6 = client.post("/call/end", data={"CallSid": call_id})
    assert r6.status_code == 200
    assert call_id not in session_context

# END-TO-END PNR FLOW

def test_e2e_pnr_flow():
    cid = "e2e002"

    r1 = client.post("/conversation", data={"CallSid": cid, "SpeechResult": "check pnr"})
    assert "ten digit" in r1.text.lower()

    r2 = client.post("/conversation", data={"CallSid": cid, "SpeechResult": "1234567890"})
    assert "confirmed" in r2.text.lower()

    r3 = client.post("/conversation", data={"CallSid": cid, "SpeechResult": "thank you"})
    assert "<Hangup" in r3.text

# END-TO-END CANCEL FLOW

def test_e2e_cancel_flow():
    cid = "e2e003"

    r1 = client.post("/conversation", data={"CallSid": cid, "SpeechResult": "cancel ticket"})
    assert "cancellation" in r1.text.lower()

    r2 = client.post("/conversation", data={"CallSid": cid, "SpeechResult": "bye"})
    assert "<Hangup" in r2.text


# END-TO-END UNKNOWN → FOLLOW-UP → RESOLVED

def test_e2e_unknown_then_valid():
    cid = "e2e004"

    r1 = client.post("/conversation", data={"CallSid": cid, "SpeechResult": "asdfghjk qwert"})
    assert "didn’t understand" in r1.text.lower()

    r2 = client.post("/conversation", data={"CallSid": cid, "SpeechResult": "book ticket"})
    assert "book a ticket" in r2.text.lower()
