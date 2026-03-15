# ============================================================
# generate_voice_sample.py — Create a reference voice sample
# ============================================================
# XTTS v2 needs a 5-10 second WAV file to clone a voice from.
# This script generates a sample using a built-in TTS voice
# and saves it to voices/neutral.wav (and copies for other emotions).
#
# For better quality, replace these with real voice recordings.
# ============================================================

import os
import shutil

from TTS.api import TTS
from utils import logger


def main():
    print()
    print("=" * 55)
    print("  🎤  Voice Sample Generator")
    print("=" * 55)
    print()

    voices_dir = os.path.join(os.path.dirname(__file__), "voices")
    os.makedirs(voices_dir, exist_ok=True)

    # Use a non-XTTS model to generate a reference voice sample
    # We'll use a basic TTS model to create a female voice sample
    logger.info("GEN", "Loading TTS model for sample generation...")

    # Use a simpler, single-speaker model to generate base sample
    tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC").to("cuda")

    # Generate a ~8 second sample with natural speech
    sample_text = (
        "Hey there, how's it going? "
        "I was just thinking about you, and honestly, it's pretty nice to chat like this. "
        "So tell me, what's been on your mind today?"
    )

    neutral_path = os.path.join(voices_dir, "neutral.wav")
    logger.info("GEN", "Generating voice sample...")
    tts.tts_to_file(text=sample_text, file_path=neutral_path)
    logger.success("GEN", f"Saved: {neutral_path}")

    # Copy as other emotion samples (same voice for now)
    # Replace these later with real recordings for different tones
    for emotion in ["happy", "soft", "teasing"]:
        emotion_path = os.path.join(voices_dir, f"{emotion}.wav")
        shutil.copy2(neutral_path, emotion_path)
        logger.info("GEN", f"Copied to: {emotion_path}")

    print()
    print("=" * 55)
    print("  ✅ Voice samples created!")
    print("  For better results, replace these with real")
    print("  voice recordings (5-10 seconds, WAV format).")
    print("=" * 55)
    print()


if __name__ == "__main__":
    main()
