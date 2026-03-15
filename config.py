# ============================================================
# config.py — Central configuration for Maya AI Voice Companion
# ============================================================

# --- LM Studio (Gemma 3) ---
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
LM_STUDIO_MODEL = "gemma-3-4b"
LLM_TEMPERATURE = 0.8
LLM_MAX_TOKENS = 150
CONVERSATION_HISTORY_LENGTH = 6  # Keep last 6 messages (3 user + 3 assistant)

# --- Speech-to-Text (Faster-Whisper) ---
WHISPER_MODEL = "base"
WHISPER_DEVICE = "cuda"  # "cuda" or "cpu" — switch to "cpu" if VRAM is tight
WHISPER_COMPUTE_TYPE = "float16"  # "float16" for GPU, "int8" for CPU

# --- Voice Activity Detection ---
USE_VAD = True  # Set to False to fall back to simple silence detection
VAD_THRESHOLD = 0.5  # Silero VAD confidence threshold (0.0 - 1.0)
SILENCE_AFTER_SPEECH = 0.8  # Seconds of silence after speech ends before processing

# --- Simple Silence Fallback ---
SILENCE_THRESHOLD_DB = -40  # dB threshold below which audio is considered silence
SILENCE_DURATION = 1.5  # Seconds of silence before processing (fallback mode)

# --- Text-to-Speech (XTTS v2) ---
TTS_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"
TTS_LANGUAGE = "en"

# --- Audio Settings ---
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1
AUDIO_CHUNK_DURATION = 0.5  # seconds per audio chunk

# --- Emotion Voices ---
VOICE_SAMPLES = {
    "neutral": "voices/neutral.wav",
    "happy": "voices/happy.wav",
    "soft": "voices/soft.wav",
    "teasing": "voices/teasing.wav",
}
DEFAULT_EMOTION = "neutral"

# --- Emotion Volume ---
# Volume multiplier per emotion (1.0 = normal)
EMOTION_VOLUME = {
    "neutral": 1.0,
    "happy": 1.3,
    "soft": 0.6,
    "teasing": 1.2,
}

# --- Thinking Delay ---
THINKING_DELAY_MIN = 1.0  # seconds
THINKING_DELAY_MAX = 2.0  # seconds

# --- Paths ---
PERSONALITY_PROMPT_PATH = "prompts/personality.txt"
CACHE_DIR = "cache"

# --- Background Music ---
BGM_VOLUME = 0.15  # Very low (0.0 - 1.0) — it's ambient background
