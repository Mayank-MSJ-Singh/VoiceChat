# ============================================================
# utils/queues.py — Central queue definitions
# ============================================================
# All worker threads communicate through these queues.
# Import this module to access shared queues.
# ============================================================

import queue


# Mic audio chunks → Speech-to-Text
audio_queue = queue.Queue()

# Transcribed text → LLM conversation engine
speech_queue = queue.Queue()

# LLM response (raw with emotion tag) → TTS processing
llm_queue = queue.Queue()

# Generated audio file path → Audio playback
playback_queue = queue.Queue()
