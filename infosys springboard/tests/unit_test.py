import pytest
from ivr_backend import detect_intent_regex, next_step, session_context
from fastapi import Response

def test_detect_intent_book_ticket():
    assert detect_intent_regex("I want to book a ticket") == "book_ticket"

def test_detect_intent_check_pnr():
    assert detect_intent_regex("check my PNR status") == "check_pnr"

def test_detect_intent_cancel():
    assert detect_intent_regex("cancel my reservation") == "cancel_ticket"

def test_detect_intent_unknown():
    assert detect_intent_regex("something random") == "unknown"

@pytest.mark.asyncio
async def test_next_step_follow_up():
    call_id = "test123"
    session_context[call_id] = {"last_intent": "book_ticket"}
    resp = next_step(call_id, "AC class please")
    assert isinstance(resp, Response)
    assert "A C class" in resp.body.decode()
