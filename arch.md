# AI Companion (Live Voice Chat) — MVP Architecture

## Goal

Build a **local real-time AI voice companion** capable of natural conversation with the user.

The system must support:

- continuous microphone listening
- real-time speech recognition
- conversational AI responses
- emotional voice synthesis
- interruptible conversation

The interaction should feel like a **live phone call**, not push-to-talk.

---

# Technology Stack

| Component           | Technology     |
| ------------------- | -------------- |
| LLM (Conversation)  | Gemma 3        |
| Local Model Runtime | LM Studio      |
| Speech-to-Text      | Faster‑Whisper |
| Text-to-Speech      | XTTS v2        |
| Language            | Python         |

Everything runs **locally**.

---

# System Architecture

```
Microphone
   ↓
Audio Listener
   ↓
Speech Recognition (Whisper)
   ↓
Conversation Engine (Gemma)
   ↓
Emotion Engine
   ↓
Speech Generation (XTTS)
   ↓
Speaker Output
```

All components operate **in parallel** to allow real-time interaction.

---

# Project Folder Structure

```
VoiceChat/
│
├── main.py
├── config.py
├── requirements.txt
│
├── core/
│   ├── audio_listener.py
│   ├── speech_to_text.py
│   ├── llm_engine.py
│   ├── emotion_engine.py
│   ├── tts_engine.py
│   ├── audio_output.py
│   └── thinking_delay.py
│
├── prompts/
│   └── personality.txt
│
├── voices/
│   ├── neutral.wav
│   ├── soft.wav
│   ├── happy.wav
│   └── teasing.wav
│
├── cache/
│   ├── input.wav
│   └── response.wav
│
└── utils/
    ├── queues.py
    └── logger.py
```

---

# Config File

**config.py**

Central configuration for the system.

Example:

```python
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"

WHISPER_MODEL = "base"
TTS_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"

AUDIO_SAMPLE_RATE = 16000

THINKING_DELAY_MIN = 1.0
THINKING_DELAY_MAX = 2.0
```

---

# Personality Prompt

**prompts/personality.txt**

```
You are Maya.

You speak casually and warmly.

Rules:
- Keep responses short (1–3 sentences)
- Speak like real texting
- Use pauses like "..."
- Occasionally stretch words like "sooo" or "and theeen"
- Ask follow-up questions
- Be playful and curious
```

This keeps responses natural.

---

# Core Modules

## 1. audio_listener.py

Responsibilities:

- capture microphone audio continuously
- split audio into chunks (~0.5 seconds)
- push audio chunks into `audio_queue`

Audio format:

- 16kHz
- mono

---

## 2. speech_to_text.py

Uses Faster-Whisper.

Responsibilities:

- read chunks from `audio_queue`
- transcribe speech
- detect sentence completion
- push text into `speech_queue`

Recommended model:

```
base
```

---

## 3. llm_engine.py

Handles conversation using Gemma.

Gemma is served by LM Studio.

API endpoint example:

```
http://localhost:1234/v1/chat/completions
```

Request format:

```
{
 "model": "gemma-3",
 "messages": [
   {"role":"system","content":"<personality prompt>"},
   {"role":"user","content":"<user message>"}
 ]
}
```

Responsibilities:

- receive user text
- maintain conversation history
- send request to LLM
- return AI reply

Conversation history should include the **last 6 messages**.

---

## 4. emotion_engine.py

Purpose:

Select the appropriate voice tone.

Simple logic:

```
if "haha" in text → happy voice
if "..." in text → soft voice
if "!" in text → excited voice
else → neutral voice
```

Output:

```
voices/<selected_voice>.wav
```

---

## 5. tts_engine.py

Uses XTTS v2.

Installation:

```
pip install TTS
```

Model:

```
tts_models/multilingual/multi-dataset/xtts_v2
```

Responsibilities:

- receive response text
- select voice sample
- generate speech
- save audio to `cache/response.wav`
- push audio path to playback queue

Voice samples must be **5–10 seconds long**.

---

## 6. audio_output.py

Responsibilities:

- read generated audio from playback queue
- play audio through speakers
- support interruption if the user starts speaking

---

## 7. thinking_delay.py

Purpose:

Simulate human response time.

Example:

```
random delay between 1–2 seconds
```

This prevents robotic instant replies.

---

# Queue System

Workers communicate through queues.

Queues required:

```
audio_queue
speech_queue
llm_queue
tts_queue
playback_queue
```

Data flow:

```
audio_queue
   ↓
speech_queue
   ↓
llm_queue
   ↓
tts_queue
   ↓
playback_queue
```

---

# Worker Threads

To enable real-time conversation:

```
Thread 1 → Audio Capture
Thread 2 → Speech Recognition
Thread 3 → Conversation Engine
Thread 4 → Voice Generation
Thread 5 → Audio Playback
```

Concurrency can be implemented with **threading or asyncio**.

---

# Interrupt System

If the user speaks while the AI is talking:

1. stop current audio playback
2. clear playback queue
3. process user speech immediately

This creates natural conversation flow.

---

# Hardware Requirements

Recommended minimum:

| Resource | Requirement                    |
| -------- | ------------------------------ |
| RAM      | 16GB (32GB available is ideal) |
| GPU      | 8GB VRAM                       |
| Storage  | ~10GB                          |

Estimated runtime usage:

| Component | Memory |
| --------- | ------ |
| Gemma     | ~4GB   |
| XTTS      | ~3GB   |
| Whisper   | ~2GB   |

Total runtime usage ≈ **9GB**.

---

# Development Phases

**Phase 1**

Gemma text conversation.

**Phase 2**

Add XTTS voice generation.

**Phase 3**

Add speech recognition.

**Phase 4**

Implement real-time voice pipeline.

**Phase 5**

Add interruption handling.

---

# MVP Scope

Included:

- real-time voice chat
- personality system
- emotion-based voice switching
- interruptible conversation

Not included:

- long-term memory
- emotional state system
- GUI
- multi-user support

---

# Expected Result

User speaks naturally into the microphone.
Speech is converted to text.
Gemma generates a conversational reply.
XTTS converts the reply into speech.
Audio is played through speakers.

The system continues listening and responding **in real time**.
