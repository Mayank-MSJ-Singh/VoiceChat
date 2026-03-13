# Maya — AI Voice Companion: Implementation Plan

> **Project**: Real-time local AI voice companion
> **Start Date**: 2026-03-13
> **Status**: In Progress

---

## Summary

Maya is a fully local, real-time AI voice companion. The user speaks into a microphone, speech is transcribed, an LLM generates a conversational reply, and the reply is synthesized back into speech — all running locally, all in real time.

---

## Hardware & Models

| Component | Spec |
|---|---|
| GPU | RTX 5060 — 8GB VRAM |
| RAM | 32GB DDR5 |
| LLM | Gemma 3 4B (Q4_K_M, 3.3GB) via LM Studio |
| STT | Faster-Whisper `base` model (~0.5GB) |
| TTS | XTTS v2 (~3GB) |
| VAD | Silero VAD (~1MB, CPU) |
| **Total VRAM** | **~6.8GB** (fits in 8GB) |

---

## Architecture

```
Microphone
   ↓
Audio Listener (Thread 1)
   ↓ audio_queue
Silero VAD + Faster-Whisper (Thread 2)
   ↓ speech_queue
Gemma 3 via LM Studio (Thread 3)
   ↓ llm_queue
Emotion Parser + XTTS v2 (Thread 4)
   ↓ playback_queue
Speaker Output (Thread 5)
```

All components run as **threads** communicating via **`queue.Queue`**.

---

## Key Design Decisions

### 1. Concurrency: Threading (not asyncio)

**Why**: Audio I/O libraries (`sounddevice`, `pyaudio`) are blocking. Threading maps naturally to our queue-based pipeline. Simpler to debug. The GIL is not a bottleneck since our work is I/O-bound (waiting for audio, LLM HTTP calls, TTS generation).

### 2. Emotion Engine: LLM-Tagged (not keyword matching)

**How**: The system prompt instructs Gemma to prefix every reply with an emotion tag:

```
[happy] Oh my god, tell me everything!
```

We parse the tag in code, select the matching voice sample, and strip the tag before sending text to TTS.

**Available emotions**: `neutral`, `happy`, `soft`, `teasing`

**Why**: The LLM understands context far better than keyword matching. "That's hilarious!" gets tagged `[happy]` even without the word "haha". Zero extra compute cost.

### 3. Sentence Completion: Silero VAD + Smart Silence (with fallback)

**Primary (VAD)**:
- Silero VAD detects speech start/end
- After speech ends → wait 0.8s of silence
- If no new speech → process the utterance

**Fallback (Simple Silence)**:
- Check audio amplitude against a volume threshold
- If below threshold for 1.5s → process
- Activated by setting `USE_VAD = False` in config

Both approaches feed into the same pipeline. Switching is one config change.

### 4. Conversation History: Last 6 Messages

Keep a sliding window of the last 6 messages (3 user + 3 assistant) to maintain context without overloading the small 4B model.

### 5. Thinking Delay: 1–2 second random pause

Prevents robotic instant replies. Makes the conversation feel more human.

---

## Folder Structure

```
VoiceChat/
├── main.py                 # Entry point — starts all threads
├── config.py               # Central configuration
├── requirements.txt        # Dependencies
│
├── core/
│   ├── audio_listener.py   # Mic capture → audio_queue
│   ├── speech_to_text.py   # VAD + Whisper → speech_queue
│   ├── llm_engine.py       # Gemma conversation → llm_queue
│   ├── emotion_engine.py   # Parse emotion tag from LLM output
│   ├── tts_engine.py       # XTTS v2 synthesis → playback_queue
│   ├── audio_output.py     # Play audio, handle interruption
│   └── thinking_delay.py   # Human-like response delay
│
├── prompts/
│   └── personality.txt     # Maya's personality prompt
│
├── voices/                 # 5-10s reference clips for XTTS
│   ├── neutral.wav
│   ├── soft.wav
│   ├── happy.wav
│   └── teasing.wav
│
├── cache/                  # Temp audio files
│   ├── input.wav
│   └── response.wav
│
└── utils/
    ├── queues.py           # Queue definitions
    └── logger.py           # Logging utility
```

---

## Development Phases

### Phase 1 — Text Chat (CLI)
Build the core conversation loop without any audio.
- [x] `config.py` — all settings
- [x] `prompts/personality.txt` — Maya's personality
- [x] `core/llm_engine.py` — Gemma API integration + conversation history
- [x] `core/emotion_engine.py` — parse `[emotion]` tags from LLM output
- [x] `main.py` — CLI chat loop (type → get reply)
- [ ] Test: Have a text conversation with Maya

### Phase 2 — Speech-to-Text
Add microphone input and transcription.
- [ ] `core/audio_listener.py` — continuous mic capture
- [ ] `core/speech_to_text.py` — Silero VAD + Faster-Whisper
- [ ] Config: `USE_VAD` flag + silence thresholds
- [ ] Test: Speak into mic → see transcribed text in console

### Phase 3 — Text-to-Speech
Add voice synthesis.
- [ ] Voice samples — record or source 4 reference clips
- [ ] `core/tts_engine.py` — XTTS v2 synthesis with emotion-based voice selection
- [ ] `core/audio_output.py` — play generated audio
- [ ] Test: Type text → hear Maya speak it back

### Phase 4 — Full Pipeline
Wire everything together with threads and queues.
- [ ] `utils/queues.py` — define all queues
- [ ] `main.py` — launch all 5 worker threads
- [ ] `core/thinking_delay.py` — random pause before reply
- [ ] End-to-end test: Speak → hear Maya reply → speak again

### Phase 5 — Interrupt Handling + Polish
- [ ] Interrupt system: stop playback when user speaks
- [ ] Edge cases: overlapping speech, empty transcriptions, LLM timeouts
- [ ] `utils/logger.py` — structured logging
- [ ] Performance tuning: latency optimization

---

## Dependencies

```
faster-whisper
TTS
sounddevice
numpy
requests
silero-vad (torch + torchaudio)
```

---

## API Reference

### LM Studio (Gemma 3)

```
POST http://localhost:1234/v1/chat/completions

{
  "model": "gemma-3-4b",
  "messages": [
    {"role": "system", "content": "<personality prompt>"},
    {"role": "user", "content": "<user message>"}
  ],
  "temperature": 0.8,
  "max_tokens": 150
}
```

---

## Risk & Mitigation

| Risk | Mitigation |
|---|---|
| VRAM overflow (~6.8GB / 8GB) | Move Whisper to CPU — runs fine with 32GB RAM |
| VAD too aggressive / too passive | Fallback to simple silence detection via config flag |
| XTTS latency too high | Cache voice model; keep responses short (1-3 sentences) |
| LM Studio connection drops | Retry logic with exponential backoff |
