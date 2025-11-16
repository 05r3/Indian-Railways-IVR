import pytest
from fastapi.testclient import TestClient
from ivr_backend import app, session_context  # Changed import from main to ivr_backend

client = TestClient(app)

def test_voice_entrypoint():
    response = client.post("/voice")
    assert response.status_code == 200
    assert "<Say>" in response.text
    assert "Welcome to Indian Railways" in response.text

def test_conversation_booking_flow():
    data = {"CallSid": "abc123", "SpeechResult": "book ticket"}
    response = client.post("/conversation", data=data)
    assert response.status_code == 200
    assert "book a ticket" in response.text or "Sleeper" in response.text

def test_conversation_check_pnr():
    data = {"CallSid": "abc124", "SpeechResult": "check PNR"}
    response = client.post("/conversation", data=data)
    assert "P N R" in response.text
    
def test_conversation_cancel_ticket():
    data = {"CallSid": "int005", "SpeechResult": "cancel my ticket"}
    response = client.post("/conversation", data=data)

    assert "cancellation request" in response.text.lower()

def test_conversation_fare_enquiry():
    data = {"CallSid": "int006", "SpeechResult": "fare enquiry"}
    response = client.post("/conversation", data=data)

    assert "train number" in response.text.lower()

def test_conversation_tatkal():
    data = {"CallSid": "int007", "SpeechResult": "tatkal"}
    response = client.post("/conversation", data=data)

    assert "tatkal booking" in response.text.lower()

def test_conversation_talk_agent():
    data = {"CallSid": "int008", "SpeechResult": "customer care"}
    response = client.post("/conversation", data=data)

    assert "connecting you to our support agent" in response.text.lower()
    assert "<Dial>" in response.text

def test_conversation_special_assistance():
    data = {"CallSid": "int009", "SpeechResult": "need help"}
    response = client.post("/conversation", data=data)

    assert "assistance team" in response.text.lower()

def test_conversation_unknown_routed_to_followup():
    data = {"CallSid": "int010", "SpeechResult": "random text"}
    response = client.post("/conversation", data=data)

    assert "didn’t understand" in response.text.lower() or "repeat" in response.text.lower()


def test_call_end_clears_context():
    data = {"CallSid": "abc125"}
    client.post("/conversation", data={"CallSid": "abc125", "SpeechResult": "book ticket"})
    resp = client.post("/call/end", data=data)
    assert resp.status_code == 200
