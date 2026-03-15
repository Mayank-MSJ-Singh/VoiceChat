# ============================================================
# core/audio_output.py — Audio playback with interruption support
# ============================================================
# Plays generated WAV files through the speakers.
# Uses a single continuous OutputStream for smooth playback.
# Supports interruption and emotion-based volume control.
# ============================================================

import wave
import numpy as np
import sounddevice as sd
import threading

from utils import logger


class AudioOutput:
    """Plays audio files through speakers, supports interruption and volume control."""

    def __init__(self):
        self.is_playing = False
        self._stop_event = threading.Event()
        logger.info("AUDIO", "Audio output ready")

    def play(self, wav_path: str, volume: float = 1.0) -> bool:
        """
        Play a WAV file through the default speakers.

        Args:
            wav_path: Path to the WAV file to play
            volume: Volume multiplier (0.0 - 2.0). 1.0 = normal.

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

            # Apply volume scaling
            if volume != 1.0:
                audio = audio * volume
                audio = np.clip(audio, -1.0, 1.0)  # Prevent clipping

            if n_channels > 1:
                audio = audio.reshape(-1, n_channels)
            else:
                audio = audio.reshape(-1, 1)

            # Use a single OutputStream for smooth, gapless playback.
            # Write audio in chunks, checking for interruption between writes.
            chunk_size = sample_rate // 4  # 250ms chunks for interrupt checks
            total_samples = len(audio)
            interrupted = False

            with sd.OutputStream(samplerate=sample_rate, channels=1, dtype="float32") as stream:
                for i in range(0, total_samples, chunk_size):
                    if self._stop_event.is_set():
                        interrupted = True
                        break

                    chunk = audio[i : i + chunk_size]
                    stream.write(chunk)

            self.is_playing = False

            if interrupted:
                logger.info("AUDIO", "Playback interrupted")
                return False

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
