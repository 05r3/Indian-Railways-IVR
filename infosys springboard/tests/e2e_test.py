import pytest
from fastapi.testclient import TestClient
from ivr_backend import app

client = TestClient(app)

def test_full_call_flow():
    call_id = "fullcall001"

    # Step 1: User dials in
    res1 = client.post("/voice")
    assert res1.status_code == 200

    # Step 2: User says "book ticket"
    res2 = client.post("/conversation", data={"CallSid": call_id, "SpeechResult": "book ticket"})
    assert "book a ticket" in res2.text

    # Step 3: User says "A C class"
    res3 = client.post("/conversation", data={"CallSid": call_id, "SpeechResult": "AC"})
    assert "A C class" in res3.text

    # Step 4: User says "thank you"
    res4 = client.post("/conversation", data={"CallSid": call_id, "SpeechResult": "thank you"})
    assert "Thank you" in res4.text

    # Step 5: End call cleanup
    res5 = client.post("/call/end", data={"CallSid": call_id})
    assert res5.status_code == 200
