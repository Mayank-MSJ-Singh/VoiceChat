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

**Next step:** User test — run `main.py` for full voice pipeline

---

## 2026-03-15 — Phase 3 TTS Fixed & Phase 4: Full Pipeline Built

### Phase 3 Resolution
- User fixed torchcodec/FFmpeg issue independently
- `test_tts.py` confirmed working ✅

### Phase 4 Files Created

| File | Purpose |
|---|---|
| `utils/queues.py` | 5 shared queues: `audio_queue`, `speech_queue`, `llm_queue` (carries text+emotion tuples), `playback_queue` |
| `core/thinking_delay.py` | Random 1-2s pause before response |
| `main.py` (rewritten) | Full pipeline with 5 worker threads + `--text` flag for CLI mode |

### Pipeline Architecture

```
Thread 1 (AudioCapture)    → mic → audio_queue
Thread 2 (SpeechToText)    → audio_queue → speech_queue
Thread 3 (LLMConversation) → speech_queue → llm_queue
Thread 4 (TTSSynthesis)    → llm_queue → playback_queue
Thread 5 (AudioPlayback)   → playback_queue → speakers
```

Graceful shutdown via `threading.Event` + Ctrl+C.

**Next step:** User test — run `main.py` and try interrupting Maya mid-sentence

---

## 2026-03-15 — Phase 5: Interrupt Handling + Polish

### How Interrupts Work

1. User speaks while Maya is talking
2. STT detects speech → pushes text to `speech_queue`
3. LLM worker checks `audio_out.is_active()` → detects Maya is speaking
4. Calls `audio_out.stop()` → playback halts within 250ms
5. Drains `llm_queue` and `playback_queue` (discards pending responses)
6. Processes the new user input immediately

### Changes

| File | Change |
|---|---|
| `main.py` | Added shared `AudioOutput` between LLM and playback workers; interrupt logic in `llm_worker`; `_drain_queue` utility |
| `core/audio_output.py` | Reduced playback chunk from 1s to 250ms for faster interrupt response |

### Status: MVP Complete 🎉

All 5 phases are done. Maya can:
- ✅ Listen to you via microphone (Silero VAD + Faster-Whisper)
- ✅ Think and respond via LLM (Gemma 3 4B via LM Studio)
- ✅ Speak back with emotion-based voice (XTTS v2)
- ✅ Be interrupted mid-sentence when you start talking
- ✅ Run entirely locally on RTX 5060 + 32GB RAM

---

## 2026-03-15 — Filler System: Natural Response Timing

### The Idea (from user)
Play pre-recorded filler audio ("hmm...", "oh really?") immediately when user stops speaking, while LLM + TTS work in background. This replaces dead silence with natural human-like thinking sounds.

### How It Works

```
User speaks → STT transcribes
                 ↓
    ┌────────────┴────────────┐
    ↓ (instant)               ↓ (takes 5-8s)
 Mood detect            Gemma → XTTS
 Pick filler            Full response
 Play "hmm..."          Generate audio
    ↓                         ↓
 🔊 FILLER plays        🔊 REAL response plays
    (covers the gap)         (follows filler)
```

### Files

| File | Purpose |
|---|---|
| `core/filler_engine.py` | Keyword-based mood detection → selects random filler per mood |
| `generate_fillers.py` | Pre-generates 13 filler WAV clips via XTTS with Maya's voice |
| `main.py` | Rewired: filler injected into `playback_queue` before LLM call; removed thinking delay |

### Mood Categories

| Mood | Triggers | Fillers |
|---|---|---|
| excited | "amazing", "love", "!" | "oh wow!", "oh really?", "wait what?" |
| sad | "tired", "bad", "lonely" | "aww...", "oh no..." |
| question | "what", "how", "?" | "hmm...", "well...", "let's see..." |
| intense | "need", "serious", "listen" | "oh...", "wait...", "okay..." |
| neutral | (default) | "hmm...", "well...", "sooo..." |

**Next step:** Run `generate_fillers.py` then test `main.py` with fillers
