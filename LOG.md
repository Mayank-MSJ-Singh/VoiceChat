# Maya — Development Log

> This file tracks all development activity. Each entry is timestamped and describes what was done, decisions made, and any issues encountered.

---

## 2026-03-13 — Project Kickoff

### Discussion & Planning

**What happened:**
- Reviewed `arch.md` — the original architecture document
- Discussed hardware: RTX 5060 (8GB VRAM), 32GB DDR5
- Confirmed LM Studio is set up with `gemma-3-4b` (Q4_K_M, 3.3GB)
- Estimated total VRAM usage: ~6.8GB (fits in 8GB with headroom)

**Key decisions made:**

| Decision | Choice | Reasoning |
|---|---|---|
| Concurrency | Threading | Audio libs are blocking; simpler than asyncio for this use case |
| Emotion detection | LLM-tagged (`[happy]`, `[soft]`, etc.) | More accurate than keyword matching; no extra compute |
| Sentence completion | Silero VAD + smart silence | More natural than raw silence; fallback to simple silence via config |
| LLM model | Gemma 3 4B Q4_K_M | Fits VRAM; good conversational quality for the size |
| Whisper model | `base` | Balance of speed + accuracy; can offload to CPU if VRAM tight |

**Files created:**
- `LLM.md` — Full implementation plan with phases, architecture, and design decisions
- `LOG.md` — This development log

**Next step:** Phase 1 — Build text chat (config, personality prompt, LLM engine, CLI loop)

---

## 2026-03-13 — Phase 1: Text Chat CLI Built

### Files Created

| File | Purpose |
|---|---|
| `config.py` | Central config — LM Studio URL, model settings, audio params, emotion voice paths |
| `prompts/personality.txt` | Maya's personality prompt with emotion tagging instructions + examples |
| `core/__init__.py` | Package init |
| `core/llm_engine.py` | Gemma 3 conversation engine — API calls, conversation history (sliding window of 6) |
| `core/emotion_engine.py` | Regex parser for `[emotion]` tags from LLM output + voice sample selector |
| `utils/__init__.py` | Package init |
| `utils/logger.py` | Colored console logger with special chat display for user/Maya messages |
| `main.py` | CLI entry point — chat loop with thinking delay, emotion parsing, graceful exit |
| `requirements.txt` | Phase 1 dep: `requests` (future phases commented out) |

### Setup

- Created Python venv at `venv/`
- Installed `requests` via pip
- Created `cache/` directory

### Verification

- All imports pass ✅
- Emotion parser correctly extracts `[happy]` from tagged text ✅
- Emotion parser falls back to `neutral` for untagged text ✅

**Next step:** User test — run `test_stt.py` to verify mic → text works

---

## 2026-03-13 — Phase 2: Speech-to-Text Built

### Dependencies Installed

- `torch 2.10.0+cu128` (CUDA enabled ✅)
- `torchaudio`
- `faster-whisper`
- `sounddevice` (31 audio devices detected, default: Realtek Microphone Array)
- `numpy`

### Files Created

| File | Purpose |
|---|---|
| `core/audio_listener.py` | Continuous mic capture via `sounddevice` callback → pushes float32 mono chunks to `audio_queue` |
| `core/speech_to_text.py` | Dual-mode speech detection (Silero VAD or simple amplitude) + Faster-Whisper transcription |
| `test_stt.py` | Standalone test script: speak into mic → see transcribed text in console |

### Design

- **VAD mode (default)**: Silero VAD detects speech start/end → 0.8s silence timeout → transcribe
- **Simple mode (fallback)**: Amplitude threshold → 1.5s silence timeout → transcribe
- Switch via `config.USE_VAD = False`
- Whisper runs on GPU (CUDA), can be moved to CPU via `config.WHISPER_DEVICE = "cpu"`

**Next step:** User test — run `generate_voice_sample.py` then `test_tts.py`

---

## 2026-03-13 — Phase 3: Text-to-Speech Built

### Dependency Issues Resolved

- `pip install TTS` failed (requires Python < 3.13)
- User found `coqui-tts` (community fork, Python 3.13 compatible) ✅
- Had to pin `transformers<5` (v5 broke coqui-tts imports)
- Had to install `coqui-tts[codec]` (torchcodec required by PyTorch 2.9+)

### Files Created

| File | Purpose |
|---|---|
| `core/tts_engine.py` | XTTS v2 synthesis with emotion-based voice selection + multi-level fallback |
| `core/audio_output.py` | WAV playback via sounddevice with chunked output for interruption support |
| `generate_voice_sample.py` | Creates initial voice reference samples using built-in TTS model |
| `test_tts.py` | Test script: type text with `[emotion]` tag → hear Maya speak |

**Next step:** User test — run `generate_voice_sample.py` then `test_tts.py`
