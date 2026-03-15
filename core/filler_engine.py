# ============================================================
# core/filler_engine.py — Instant filler audio while TTS works
# ============================================================
# Detects the mood/intent of user speech and immediately plays
# a pre-recorded filler audio ("hmm...", "oh really?", etc.)
# to fill the silence while the full LLM + TTS pipeline runs.
#
# This makes conversation feel alive — like a human going
# "hmm..." while thinking of what to say.
# ============================================================

import os
import random

import config
from utils import logger


# ============================================================
# Mood-based filler mapping
# ============================================================
# Each mood has a list of filler audio filenames.
# The engine picks one randomly for variety.

FILLER_MAP = {
    "excited": [
        "oh_wow.wav",
        "oh_really.wav",
        "wait_what.wav",
    ],
    "sad": [
        "aww.wav",
        "oh_no.wav",
        "hmm_soft.wav",
    ],
    "question": [
        "hmm.wav",
        "well.wav",
        "lets_see.wav",
    ],
    "intense": [
        "oh.wav",
        "wait.wav",
        "okay.wav",
    ],
    "neutral": [
        "hmm.wav",
        "well.wav",
        "sooo.wav",
    ],
}

# Keywords for quick mood detection (no LLM call needed = instant)
MOOD_KEYWORDS = {
    "excited": ["amazing", "awesome", "great", "love", "best", "fantastic", "incredible",
                "wow", "cool", "nice", "happy", "excited", "!"],
    "sad": ["sad", "tired", "rough", "bad", "worst", "hate", "boring", "lonely",
            "miss", "depressed", "crying", "hurt", "sorry"],
    "question": ["what", "how", "why", "when", "where", "who", "which", "?",
                 "should", "could", "would", "can", "do you", "are you", "is it"],
    "intense": ["need", "important", "serious", "listen", "stop", "wait",
                "actually", "honestly", "real", "truth", "problem"],
}


class FillerEngine:
    """Selects and provides filler audio based on user mood."""

    def __init__(self):
        self.fillers_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "fillers",
        )

        # Check which fillers are available
        self.available = {}
        if os.path.exists(self.fillers_dir):
            for mood, files in FILLER_MAP.items():
                available_files = [
                    f for f in files
                    if os.path.exists(os.path.join(self.fillers_dir, f))
                ]
                if available_files:
                    self.available[mood] = available_files

        if self.available:
            total = sum(len(v) for v in self.available.values())
            logger.success("FILLER", f"Loaded {total} filler audio files")
        else:
            logger.warn("FILLER", "No filler audio found — run generate_fillers.py first")

    def detect_mood(self, text: str) -> str:
        """
        Quick mood detection from user text using keyword matching.
        Zero latency — no LLM call needed.
        """
        text_lower = text.lower()

        # Check each mood's keywords
        scores = {}
        for mood, keywords in MOOD_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[mood] = score

        if scores:
            return max(scores, key=scores.get)

        return "neutral"

    def get_filler(self, text: str) -> str | None:
        """
        Get a filler audio path based on user text mood.

        Args:
            text: User's transcribed speech

        Returns:
            Path to filler WAV file, or None if no fillers available
        """
        if not self.available:
            return None

        mood = self.detect_mood(text)

        # Get fillers for this mood (fall back to neutral)
        fillers = self.available.get(mood, self.available.get("neutral", []))

        if not fillers:
            # Fall back to any available filler
            all_fillers = [f for files in self.available.values() for f in files]
            if not all_fillers:
                return None
            fillers = all_fillers

        chosen = random.choice(fillers)
        path = os.path.join(self.fillers_dir, chosen)

        logger.info("FILLER", f"[{mood}] → {chosen}")
        return path
