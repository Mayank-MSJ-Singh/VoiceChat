# ============================================================
# core/audio_listener.py — Continuous microphone capture
# ============================================================
# Captures audio from the default microphone in real-time,
# splits it into chunks, and pushes them into audio_queue.
# Supports both threaded pipeline and standalone testing.
# ============================================================

import numpy as np
import sounddevice as sd

import config
from utils import logger


class AudioListener:
    """Captures microphone audio and pushes chunks to a queue."""

    def __init__(self, audio_queue):
        """
        Args:
            audio_queue: queue.Queue to push audio chunks into
        """
        self.audio_queue = audio_queue
        self.sample_rate = config.AUDIO_SAMPLE_RATE
        self.channels = config.AUDIO_CHANNELS
        self.chunk_samples = int(self.sample_rate * config.AUDIO_CHUNK_DURATION)
        self.running = False

        logger.info("MIC", f"Sample rate: {self.sample_rate}Hz, Chunk: {config.AUDIO_CHUNK_DURATION}s")

    def _audio_callback(self, indata, frames, time_info, status):
        """Called by sounddevice for each audio chunk."""
        if status:
            logger.warn("MIC", f"Audio status: {status}")

        # Copy the audio data (indata is a view that gets recycled)
        audio_chunk = indata[:, 0].copy()  # mono: take first channel
        self.audio_queue.put(audio_chunk)

    def start(self):
        """Start capturing audio (blocking — run in a thread)."""
        self.running = True
        logger.success("MIC", "Listening... (speak into your microphone)")

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="float32",
                blocksize=self.chunk_samples,
                callback=self._audio_callback,
            ):
                # Keep the stream open until stopped
                while self.running:
                    sd.sleep(100)  # Sleep 100ms between checks
        except Exception as e:
            logger.error("MIC", f"Audio capture error: {e}")
            self.running = False

    def stop(self):
        """Stop capturing audio."""
        self.running = False
        logger.info("MIC", "Stopped listening")
