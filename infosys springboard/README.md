#  Indian Railways IVR Modernization using Conversational AI (ACS/BAP Integration)

##  Project Overview

This project modernizes a legacy IVR system built on VoiceXML (VXML)  by integrating it with modern Conversational AI platforms (ACS/BAP).  
It enables natural, voice-driven user interactions while reusing existing IVR assets — reducing redevelopment effort and improving user experience.

While the original project statement references Azure Communication Services (ACS) and Business Application Platform (BAP), this implementation uses Twilio Voice API to perform those same communication and voice functions — allowing real-time, speech-based interaction between callers and an AI-enabled backend.

---

##  Project Objectives

- Integrate VXML-based IVR systems with Conversational AI platforms (ACS/BAP)
- Enable conversational interactions within traditional IVR frameworks
- Minimize rework during the modernization process
- Improve usability and voice-driven customer experience

---

## Technologies Used

| Component | Technology |
|------------|-------------|
| Backend / Middleware | **FastAPI (Python)** |
| Telephony / IVR Gateway | **Twilio Voice API** (simulating legacy VXML IVR) |
| Conversational AI Layer | Keyword + Context-based Engine (AI-ready) |
| Frontend Console | HTML + JS call launcher |
| Optional AI Platform | Azure ACS / BAP / OpenAI (can be integrated) |

---

##  Module 1 — Legacy System Analysis and Requirements Gathering

### Objective
Assess the architecture and limitations of existing **VXML-based IVR** systems and define integration requirements for ACS/BAP.

###  Key Deliverables
- Documentation of legacy IVR components (PBX, VXML server, ASR/TTS, backend APIs)
- Identification of functional gaps and integration challenges
- Definition of integration flow between IVR ↔ Middleware ↔ ACS/BAP

###  Outcome
Provides a  blueprint for connecting legacy IVRs to modern Conversational AI platforms with minimal rework.



—

### Implementation Linkages
The following points from Module 1 are **implemented in Modules 2 and 3**:

| Module 1 Finding | Implemented In | How |
|------------------|----------------|-----|
| IVR → Middleware → AI flow | **Module 2 + 3** | FastAPI + Twilio webhooks handle voice input and AI responses |
| Real-time voice handling | **Module 2** | Twilio `SpeechResult` delivers speech text instantly |
| Session management | **Module 2 + 3** | `session_context` dictionary tracks call context |
| Grammar limits → Free speech | **Module 3** | Intent detection with flexible keyword mapping |
| Agent transfer | **Module 2** | `resp.dial()` connects to live representative |
| Integration challenges | **Module 2 + 3** | Solved through lightweight APIs and async flow |



## 🔗 Module 2 — Integration Layer Development

###  Objective
Build a **middleware/API layer** to connect legacy VXML systems with the Conversational AI stack.

###  Implementation Highlights
- **FastAPI backend** that serves as the Integration Layer
- **Endpoints**:
  - `/conversation` → handles speech and contextual flow
  - `/call/start` → initiates outbound test calls
- **Real-time data handling** using Twilio Voice webhooks
- **Session management** maintained via in-memory `session_context`

###  Validation
- Tested with Twilio inbound/outbound calls
- Verified menu-to-AI transition flow
- Ready for integration with ACS or BAP



---

## 🗣️ Module 3 — Conversational AI Interface Development

###  Objective
Introduce **natural language conversation** into the IVR system through AI-powered flows.

###  Features
- Speech recognition via Twilio (`SpeechResult`)
- Intent detection (`INTENT_KEYWORDS`)
- Context-aware responses via `next_step()`
- Optional integration with AI (e.g., Azure Language, OpenAI GPT)

###  Flow Summary
1. User speaks to IVR → Twilio converts speech to text  
2. Backend detects intent → responds contextually  
3. AI or rule-based logic generates natural responses  
4. Twilio converts reply to voice output for caller  



---

##  Frontend – IVR Call Launcher

A simple web console for initiating outbound calls via the backend.

- File: `index.html`
- Action: Sends POST `/call/start` request to backend
- Input: Phone number in `+91XXXXXXXXXX` format
- Displays call status and Twilio SID in browser

---
## Module 4 — Testing & Validation

Objective:
Ensure the IVR backend behaves correctly across unit, integration, end-to-end, error handling, and load testing.

## Test Categories:

Unit Tests (unit_test.py)

Intent detection: book_ticket, check_pnr, cancel_ticket, unknown input

Context-based next step responses

Session management validation

Integration Tests (integration_test.py)

/voice endpoint returns <Say>

/conversation handles booking and PNR queries

/call/end clears session context

End-to-End (E2E) Tests (e2e_tests.py)

Simulates full call flow: voice → booking → class selection → thank you → call end

Error Handling Tests (errorhandling_Test.py)

Missing input

Invalid endpoints

Missing call parameters

Load Testing (load_test.py)

Simulates multiple users calling the IVR concurrently

Uses Locust to stress test /voice and /conversation endpoints

Validation Results:
All tests passed successfully, confirming backend correctness, session handling, and conversation logic.

Reference Files:

unit_test.py

integration_test.py

e2e_tests.py

errorhandling_Test.py

load_test.py

## How to Run Tests
# Unit, Integration, E2E, Error Handling
pytest tests/

# Load Testing
locust -f tests/load_test.py


Note: Load testing requires the backend to be running at the specified URL.

## Project Outcome

Modernized legacy IVR with conversational AI

Fully tested backend with unit, integration, E2E, error handling, and load tests

Session-aware, context-sensitive IVR interactions

Ready for production deployment and future AI platform integration
