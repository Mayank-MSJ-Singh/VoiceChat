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

**Next step:** User test — run `main.py` with LM Studio running to have a text conversation with Maya
