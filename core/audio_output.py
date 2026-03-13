# ============================================================
# core/audio_output.py — Audio playback with interruption support
# ============================================================
# Plays generated WAV files through the speakers.
# Supports interruption when the user starts speaking.
# ============================================================

import wave
import numpy as np
import sounddevice as sd
import threading

from utils import logger


class AudioOutput:
    """Plays audio files through speakers, supports interruption."""

    def __init__(self):
        self.is_playing = False
        self._stop_event = threading.Event()
        logger.info("AUDIO", "Audio output ready")

    def play(self, wav_path: str) -> bool:
        """
        Play a WAV file through the default speakers.

        Args:
            wav_path: Path to the WAV file to play

        Returns:
            True if played fully, False if interrupted or error
        """
        if not wav_path:
            return False

        self._stop_event.clear()
        self.is_playing = True

        try:
            # Read WAV file
            with wave.open(wav_path, "rb") as wf:
                sample_rate = wf.getframerate()
                n_channels = wf.getnchannels()
                n_frames = wf.getnframes()
                audio_data = wf.readframes(n_frames)

            # Convert to numpy array
            audio = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

            if n_channels > 1:
                audio = audio.reshape(-1, n_channels)

            # Play in chunks so we can check for interruption
            chunk_size = sample_rate  # 1 second chunks
            total_samples = len(audio)

            for i in range(0, total_samples, chunk_size):
                if self._stop_event.is_set():
                    logger.info("AUDIO", "Playback interrupted")
                    self.is_playing = False
                    return False

                chunk = audio[i : i + chunk_size]
                sd.play(chunk, samplerate=sample_rate)
                sd.wait()

            self.is_playing = False
            return True

        except Exception as e:
            logger.error("AUDIO", f"Playback error: {e}")
            self.is_playing = False
            return False

    def stop(self):
        """Interrupt current playback."""
        self._stop_event.set()
        sd.stop()
        self.is_playing = False

    def is_active(self) -> bool:
        """Check if audio is currently playing."""
        return self.is_playing
