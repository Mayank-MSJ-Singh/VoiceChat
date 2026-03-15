# ============================================================
# core/bgm_player.py — Continuous background music player
# ============================================================
# Plays ambient background music in a loop at low volume.
# Runs on its own audio stream, independent of speech playback.
# Does NOT stop when Maya talks — runs continuously.
# ============================================================

import os
import threading
import numpy as np
import sounddevice as sd
import soundfile as sf

import config
from utils import logger


class BGMPlayer:
    """Loops background music at low volume throughout the session."""

    def __init__(self):
        self._stop_event = threading.Event()
        self._thread = None
        self._stream = None

        # Find BGM file
        self.bgm_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "bgm",
        )
        self.bgm_file = self._find_bgm()

        if self.bgm_file:
            logger.success("BGM", f"Found: {os.path.basename(self.bgm_file)}")
        else:
            logger.warn("BGM", "No BGM file found in bgm/ — skipping ambient music")

    def _find_bgm(self) -> str | None:
        """Find the first audio file in bgm/ directory."""
        if not os.path.exists(self.bgm_dir):
            os.makedirs(self.bgm_dir, exist_ok=True)
            return None

        for ext in (".wav", ".mp3", ".ogg", ".flac"):
            for f in sorted(os.listdir(self.bgm_dir)):
                if f.lower().endswith(ext):
                    return os.path.join(self.bgm_dir, f)

        return None

    def start(self):
        """Start BGM playback on a background thread."""
        if not self.bgm_file:
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._loop, name="BGMLoop", daemon=True
        )
        self._thread.start()

    def _loop(self):
        """Main BGM loop — reads audio, plays at low volume, repeats."""
        try:
            # Load the full audio file
            audio, sample_rate = sf.read(self.bgm_file, dtype="float32")

            # Convert to mono if stereo
            if audio.ndim > 1:
                audio = audio.mean(axis=1)

            # Apply BGM volume (very low — it's background)
            volume = config.BGM_VOLUME
            audio = (audio * volume).astype(np.float32)

            # Reshape for output stream
            audio = audio.reshape(-1, 1)

            logger.info("BGM", f"Playing at {int(volume * 100)}% volume (loops)")

            # Loop until stopped
            chunk_size = sample_rate  # Write 1 second at a time
            total_samples = len(audio)

            with sd.OutputStream(
                samplerate=sample_rate,
                channels=1,
                dtype="float32",
                device=sd.default.device[1],  # Use default output device
            ) as stream:
                while not self._stop_event.is_set():
                    # Play the track from start to end
                    for i in range(0, total_samples, chunk_size):
                        if self._stop_event.is_set():
                            return

                        chunk = audio[i : i + chunk_size]
                        stream.write(chunk)

                    # Track ended — loop back to start

        except Exception as e:
            logger.error("BGM", f"Playback error: {e}")

    def stop(self):
        """Stop BGM playback."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        logger.info("BGM", "Stopped")
