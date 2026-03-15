# ============================================================
# core/tts_engine.py — XTTS v2 voice synthesis
# ============================================================
# Converts text to speech using Coqui XTTS v2.
# Selects voice sample based on emotion tag from the LLM.
# Saves generated audio to cache for playback.
# ============================================================

import os
import numpy as np

import config
from utils import logger


class TTSEngine:
    """Text-to-speech using XTTS v2 with emotion-based voice selection."""

    def __init__(self):
        logger.info("TTS", "Loading XTTS v2 model (this may take a moment)...")

        from TTS.api import TTS

        # Load the XTTS v2 model on GPU
        self.tts = TTS(model_name=config.TTS_MODEL).to("cuda")

        # Ensure cache directory exists
        self.cache_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            config.CACHE_DIR,
        )
        os.makedirs(self.cache_dir, exist_ok=True)

        # Resolve voice sample paths (relative to project root)
        self.project_root = os.path.dirname(os.path.dirname(__file__))
        self._check_voice_samples()

        logger.success("TTS", "XTTS v2 ready")

    def _check_voice_samples(self):
        """Check which voice samples are available."""
        available = []
        missing = []

        for emotion, rel_path in config.VOICE_SAMPLES.items():
            full_path = os.path.join(self.project_root, rel_path)
            if os.path.exists(full_path):
                available.append(emotion)
            else:
                missing.append(emotion)

        if available:
            logger.info("TTS", f"Voice samples found: {', '.join(available)}")
        if missing:
            logger.warn("TTS", f"Voice samples missing: {', '.join(missing)}")
            logger.warn("TTS", "Missing voices will fall back to first available sample")

    def _get_voice_path(self, emotion: str) -> str:
        """
        Get the voice sample path for an emotion, with fallback logic.

        Falls back to: requested emotion → neutral → any available sample
        """
        # Try the requested emotion
        rel_path = config.VOICE_SAMPLES.get(emotion, config.VOICE_SAMPLES[config.DEFAULT_EMOTION])
        full_path = os.path.join(self.project_root, rel_path)

        if os.path.exists(full_path):
            return full_path

        # Fall back to neutral
        neutral_path = os.path.join(self.project_root, config.VOICE_SAMPLES[config.DEFAULT_EMOTION])
        if os.path.exists(neutral_path):
            return neutral_path

        # Fall back to any available voice sample
        for em, rp in config.VOICE_SAMPLES.items():
            fp = os.path.join(self.project_root, rp)
            if os.path.exists(fp):
                logger.warn("TTS", f"Using '{em}' voice as fallback")
                return fp

        raise FileNotFoundError(
            "No voice samples found! Add a 5-10 second WAV file to the voices/ directory."
        )

    def synthesize(self, text: str, emotion: str = "neutral") -> str:
        """
        Convert text to speech and save to cache.

        Args:
            text: The text to speak
            emotion: Emotion for voice selection ("neutral", "happy", "soft", "teasing")

        Returns:
            Path to the generated WAV file
        """
        if not text.strip():
            return ""

        # Get voice sample for this emotion
        voice_path = self._get_voice_path(emotion)

        # Output path — unique per synthesis to avoid overwrites during streaming
        import time
        output_path = os.path.join(self.cache_dir, f"tts_{int(time.time()*1000)}.wav")

        logger.info("TTS", f"Generating speech [{emotion}]: \"{text[:50]}...\"" if len(text) > 50 else f"Generating speech [{emotion}]: \"{text}\"")

        try:
            # Generate speech with XTTS v2
            self.tts.tts_to_file(
                text=text,
                speaker_wav=voice_path,
                language=config.TTS_LANGUAGE,
                file_path=output_path,
            )

            logger.success("TTS", "Audio generated")
            return output_path

        except Exception as e:
            logger.error("TTS", f"Synthesis failed: {e}")
            return ""
