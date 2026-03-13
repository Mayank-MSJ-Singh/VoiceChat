# ============================================================
# core/speech_to_text.py — VAD + Faster-Whisper transcription
# ============================================================
# Reads audio chunks from audio_queue, detects speech using
# Silero VAD (or simple silence fallback), and transcribes
# completed utterances with Faster-Whisper.
# ============================================================

import time
import numpy as np
import torch

import config
from utils import logger


class SpeechToText:
    """
    Processes audio chunks → detects speech boundaries → transcribes.

    Two modes (controlled by config.USE_VAD):
      - VAD mode: Uses Silero VAD to detect speech start/end
      - Simple mode: Uses amplitude threshold for silence detection
    """

    def __init__(self, audio_queue, speech_queue):
        """
        Args:
            audio_queue: queue.Queue of audio chunks from AudioListener
            speech_queue: queue.Queue to push transcribed text into
        """
        self.audio_queue = audio_queue
        self.speech_queue = speech_queue
        self.running = False

        # Buffer to accumulate audio during speech
        self.audio_buffer = []
        self.is_speaking = False
        self.silence_start = None

        # Load Silero VAD if enabled
        if config.USE_VAD:
            logger.info("STT", "Loading Silero VAD...")
            self.vad_model, self.vad_utils = torch.hub.load(
                repo_or_dir="snakers4/silero-vad",
                model="silero_vad",
                trust_repo=True,
            )
            self.vad_model.eval()
            logger.success("STT", "Silero VAD loaded")
        else:
            self.vad_model = None
            logger.info("STT", "Using simple silence detection (VAD disabled)")

        # Load Faster-Whisper
        logger.info("STT", f"Loading Whisper '{config.WHISPER_MODEL}' on {config.WHISPER_DEVICE}...")
        from faster_whisper import WhisperModel

        self.whisper = WhisperModel(
            config.WHISPER_MODEL,
            device=config.WHISPER_DEVICE,
            compute_type=config.WHISPER_COMPUTE_TYPE,
        )
        logger.success("STT", "Whisper model loaded")

    def _is_speech_vad(self, audio_chunk: np.ndarray) -> bool:
        """Check if audio chunk contains speech using Silero VAD."""
        # Silero VAD expects 16kHz mono float32 tensor
        audio_tensor = torch.from_numpy(audio_chunk).float()

        # VAD works best with 512-sample windows for 16kHz
        # Process in 512-sample windows, return True if any window has speech
        window_size = 512
        for i in range(0, len(audio_tensor) - window_size + 1, window_size):
            window = audio_tensor[i : i + window_size]
            confidence = self.vad_model(window, config.AUDIO_SAMPLE_RATE).item()
            if confidence > config.VAD_THRESHOLD:
                return True
        return False

    def _is_speech_simple(self, audio_chunk: np.ndarray) -> bool:
        """Check if audio chunk contains speech using amplitude threshold."""
        # Calculate RMS amplitude in dB
        rms = np.sqrt(np.mean(audio_chunk**2))
        if rms > 0:
            db = 20 * np.log10(rms)
        else:
            db = -100
        return db > config.SILENCE_THRESHOLD_DB

    def _is_speech(self, audio_chunk: np.ndarray) -> bool:
        """Detect speech using configured method (VAD or simple)."""
        if config.USE_VAD and self.vad_model is not None:
            return self._is_speech_vad(audio_chunk)
        return self._is_speech_simple(audio_chunk)

    def _transcribe(self, audio: np.ndarray) -> str:
        """Transcribe audio buffer using Faster-Whisper."""
        if len(audio) < config.AUDIO_SAMPLE_RATE * 0.3:
            # Skip very short audio (< 0.3 seconds) — probably noise
            return ""

        segments, info = self.whisper.transcribe(
            audio,
            language="en",
            beam_size=5,
            vad_filter=True,  # Whisper's built-in VAD for cleanup
        )

        text = " ".join(seg.text.strip() for seg in segments).strip()
        return text

    def start(self):
        """
        Main processing loop (blocking — run in a thread).

        Reads audio chunks, detects speech boundaries, and transcribes
        complete utterances.
        """
        self.running = True
        silence_timeout = (
            config.SILENCE_AFTER_SPEECH if config.USE_VAD else config.SILENCE_DURATION
        )
        logger.success("STT", f"Ready (silence timeout: {silence_timeout}s)")

        while self.running:
            try:
                # Get next audio chunk (with timeout so we can check self.running)
                try:
                    chunk = self.audio_queue.get(timeout=0.1)
                except Exception:
                    continue

                has_speech = self._is_speech(chunk)

                if has_speech:
                    # Speech detected — buffer it
                    if not self.is_speaking:
                        self.is_speaking = True
                        self.audio_buffer = []
                        logger.info("STT", "Speech started...")

                    self.audio_buffer.append(chunk)
                    self.silence_start = None

                elif self.is_speaking:
                    # Was speaking, now silence — start silence timer
                    self.audio_buffer.append(chunk)  # Keep buffering during silence gap

                    if self.silence_start is None:
                        self.silence_start = time.time()

                    elapsed_silence = time.time() - self.silence_start

                    if elapsed_silence >= silence_timeout:
                        # Silence timeout reached — transcribe the utterance
                        self.is_speaking = False
                        self.silence_start = None

                        # Concatenate buffered audio
                        full_audio = np.concatenate(self.audio_buffer)
                        self.audio_buffer = []

                        # Transcribe
                        text = self._transcribe(full_audio)

                        if text:
                            logger.info("STT", f"Heard: \"{text}\"")
                            self.speech_queue.put(text)
                        else:
                            logger.warn("STT", "Empty transcription — skipped")

            except Exception as e:
                logger.error("STT", f"Error: {e}")
                continue

    def stop(self):
        """Stop processing."""
        self.running = False
        logger.info("STT", "Stopped")
