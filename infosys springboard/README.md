#  Indian Railways IVR Modernization using Conversational AI (ACS/BAP Integration)

##  Project Overview

This project modernizes a legacy IVR system built on VoiceXML (VXML)  by integrating it with modern Conversational AI platforms (ACS/BAP).  
It enables natural, voice-driven user interactions while reusing existing IVR assets — reducing redevelopment effort and improving user experience.

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

 _Refer to:_ `Module1_Legacy_Analysis.docx`

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

 _Refer to:_ `indian_railways_ivr_backend.py`

---

## 🗣️ Module 3 — Conversational AI Interface Development

###  Objective
Introduce **natural language conversation** into the IVR system through AI-powered flows.

###  Features
- Speech recognition via Twilio (`SpeechResult`)
- Intent detection (`INTENT_KEYWORDS`)
- Context-aware responses via `next_step()`
- Support for both speech and DTMF inputs
- Optional integration with AI (e.g., Azure Language, OpenAI GPT)

###  Flow Summary
1. User speaks to IVR → Twilio converts speech to text  
2. Backend detects intent → responds contextually  
3. AI or rule-based logic generates natural responses  
4. Twilio converts reply to voice output for caller  

📄 _Refer to:_ `ivr_backend.py`

---

##  Frontend – IVR Call Launcher

A simple web console for initiating outbound calls via the backend.

- File: `index.html`
- Action: Sends POST `/call/start` request to backend
- Input: Phone number in `+91XXXXXXXXXX` format
- Displays call status and Twilio SID in browser

---

