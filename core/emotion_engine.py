# ============================================================
# core/emotion_engine.py — Parse emotion tags from LLM output
# ============================================================
# The LLM is prompted to prefix every reply with [emotion].
# This module extracts the tag and returns the clean text + emotion.
# ============================================================

import re
import config


# Regex to match emotion tags like [happy], [soft], [neutral], [teasing]
EMOTION_PATTERN = re.compile(r"^\s*\[(\w+)\]\s*", re.IGNORECASE)

# Valid emotions (must match keys in config.VOICE_SAMPLES)
VALID_EMOTIONS = set(config.VOICE_SAMPLES.keys())


def parse_emotion(text: str) -> tuple[str, str]:
    """
    Extract emotion tag from LLM response.

    Args:
        text: Raw LLM response, e.g. "[happy] Oh my god, that's amazing!"

    Returns:
        Tuple of (clean_text, emotion)
        e.g. ("Oh my god, that's amazing!", "happy")
    """
    match = EMOTION_PATTERN.match(text)

    if match:
        emotion = match.group(1).lower()
        clean_text = text[match.end():]

        # If the LLM hallucinated an unknown emotion, fall back to default
        if emotion not in VALID_EMOTIONS:
            emotion = config.DEFAULT_EMOTION

        return clean_text.strip(), emotion

    # No tag found — return as-is with default emotion
    return text.strip(), config.DEFAULT_EMOTION


def get_voice_sample(emotion: str) -> str:
    """
    Get the voice sample file path for a given emotion.

    Args:
        emotion: One of "neutral", "happy", "soft", "teasing"

    Returns:
        Path to the voice WAV file
    """
    return config.VOICE_SAMPLES.get(emotion, config.VOICE_SAMPLES[config.DEFAULT_EMOTION])
