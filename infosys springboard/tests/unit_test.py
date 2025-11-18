import pytest
from fastapi import Response
from main import detect_intent, next_step, session_context


# =========================================================
# UNIT TESTS FOR INTENT DETECTION
# =========================================================

def test_detect_intent_book_ticket():
    assert detect_intent("I want to book a ticket") == "book_ticket"


def test_detect_intent_check_pnr():
    assert detect_intent("check my PNR status") == "check_pnr"


def test_detect_intent_cancel():
    assert detect_intent("cancel my reservation") == "cancel_ticket"


def test_detect_intent_fare():
    assert detect_intent("what is the fare") == "fare_enquiry"


def test_detect_intent_tatkal():
    assert detect_intent("tatkal details please") == "tatkal_info"


def test_detect_intent_agent():
    assert detect_intent("connect me to customer care") == "talk_agent"


def test_detect_intent_assistance():
    assert detect_intent("I need assistance") == "special_assistance"


def test_detect_intent_train_live_status():
    assert detect_intent("where is the train running now") == "train_live_status"


def test_detect_intent_platform_locator():
    assert detect_intent("which platform for my train") == "platform_locator"


def test_detect_intent_digit_mapping():
    assert detect_intent("1") == "book_ticket"
    assert detect_intent("9") == "platform_locator"


def test_detect_intent_unknown():
    assert detect_intent("completely random text") == "unknown"


# =========================================================
# UNIT TESTS FOR next_step()
# =========================================================

@pytest.mark.asyncio
async def test_next_step_ac_class():
    call_id = "u1"
    session_context[call_id] = {"last_intent": "book_ticket"}

    resp = next_step(call_id, "AC")

    assert isinstance(resp, Response)
    body = resp.body.decode()
    assert "A C class" in body
    assert session_context[call_id]["booking_class"] == "AC"


@pytest.mark.asyncio
async def test_next_step_sleeper_class():
    call_id = "u2"
    session_context[call_id] = {"last_intent": "book_ticket"}

    resp = next_step(call_id, "sleeper")

    assert "Sleeper class" in resp.body.decode()
    assert session_context[call_id]["booking_class"] == "Sleeper"


@pytest.mark.asyncio
async def test_next_step_booking_date():
    call_id = "u3"
    session_context[call_id] = {"last_intent": "book_ticket"}

    resp = next_step(call_id, "15 November")
    body = resp.body.decode()

    assert "Booking date" in body
    # normalized to lowercase in next_step
    assert session_context[call_id]["booking_date"] == "15 november"


@pytest.mark.asyncio
async def test_next_step_invalid_booking_reply():
    call_id = "u4"
    session_context[call_id] = {"last_intent": "book_ticket"}

    resp = next_step(call_id, "blah blah")
    assert "Please specify your class" in resp.body.decode()


# =========================================================
# UNIT TESTS FOR PNR FOLLOW-UP LOGIC
# =========================================================

@pytest.mark.asyncio
async def test_valid_pnr_followup():
    call_id = "u5"
    session_context[call_id] = {"last_intent": "check_pnr"}

    resp = next_step(call_id, "1234567890")
    body = resp.body.decode()

    assert "confirmed" in body.lower()
    assert "pnr" in body.lower()


@pytest.mark.asyncio
async def test_invalid_pnr_short():
    call_id = "u6"
    session_context[call_id] = {"last_intent": "check_pnr"}

    resp = next_step(call_id, "123")
    assert "valid ten digit P N R" in resp.body.decode()


@pytest.mark.asyncio
async def test_invalid_pnr_non_numeric():
    call_id = "u7"
    session_context[call_id] = {"last_intent": "check_pnr"}

    resp = next_step(call_id, "ABC123")
    assert "valid ten digit P N R" in resp.body.decode()


# =========================================================
# UNIT TESTS FOR ENDING CONVERSATION
# =========================================================

@pytest.mark.asyncio
async def test_end_conversation_thank_you():
    call_id = "u8"
    session_context[call_id] = {"last_intent": "book_ticket"}

    resp = next_step(call_id, "thank you")
    body = resp.body.decode()

    assert "Thank you for using Indian Railways" in body
    assert "<Hangup" in body


@pytest.mark.asyncio
async def test_end_conversation_bye():
    call_id = "u9"
    session_context[call_id] = {"last_intent": "check_pnr"}

    resp = next_step(call_id, "bye")
    assert "<Hangup" in resp.body.decode()


# =========================================================
# UNKNOWN / FALLBACK BEHAVIOR
# =========================================================

@pytest.mark.asyncio
async def test_next_step_no_context_unknown():
    call_id = "u10"
    session_context[call_id] = {}

    resp = next_step(call_id, "nonsense words")
    assert "didn’t understand" in resp.body.decode()


@pytest.mark.asyncio
async def test_next_step_unknown_with_context():
    call_id = "u11"
    session_context[call_id] = {"last_intent": "book_ticket"}

    resp = next_step(call_id, "??")
    assert "Please specify your class" in resp.body.decode()
