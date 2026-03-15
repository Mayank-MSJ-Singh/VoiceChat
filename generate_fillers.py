# ============================================================
# generate_fillers.py — Pre-generate filler audio files
# ============================================================
# Creates short filler audio clips ("hmm", "well", "oh wow")
# using XTTS v2 with the same voice as Maya.
#
# Run this once before using voice mode with fillers.
# ============================================================

import os

from TTS.api import TTS
from utils import logger


# Filler texts to generate — kept short for quick playback
FILLERS = {
    # Neutral / thinking
    "hmm.wav": "Hmm...",
    "well.wav": "Well...",
    "sooo.wav": "Sooo...",

    # Excited
    "oh_wow.wav": "Oh wow!",
    "oh_really.wav": "Oh really?",
    "wait_what.wav": "Wait, what?",

    # Sad / empathetic
    "aww.wav": "Aww...",
    "oh_no.wav": "Oh no...",
    "hmm_soft.wav": "Hmm...",

    # Intense
    "oh.wav": "Oh...",
    "wait.wav": "Wait...",
    "okay.wav": "Okay...",

    # Extra variety
    "lets_see.wav": "Let's see...",
}


def main():
    print()
    print("=" * 55)
    print("  🎤  Filler Audio Generator")
    print("=" * 55)
    print()

    fillers_dir = os.path.join(os.path.dirname(__file__), "fillers")
    os.makedirs(fillers_dir, exist_ok=True)

    # Use same voice as Maya's neutral voice for consistency
    voice_path = os.path.join(os.path.dirname(__file__), "voices", "neutral.wav")
    if not os.path.exists(voice_path):
        print("ERROR: voices/neutral.wav not found!")
        print("Run generate_voice_sample.py first.")
        return

    # Load TTS
    logger.info("GEN", "Loading XTTS v2...")
    tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2").to("cuda")
    logger.success("GEN", "Ready")

    # Generate each filler
    for filename, text in FILLERS.items():
        output_path = os.path.join(fillers_dir, filename)

        if os.path.exists(output_path):
            logger.info("GEN", f"Skipping {filename} (already exists)")
            continue

        logger.info("GEN", f"Generating: {filename} → \"{text}\"")
        try:
            tts.tts_to_file(
                text=text,
                speaker_wav=voice_path,
                language="en",
                file_path=output_path,
            )
            logger.success("GEN", f"Saved: {filename}")
        except Exception as e:
            logger.error("GEN", f"Failed {filename}: {e}")

    print()
    print("=" * 55)
    print(f"  ✅ Filler audio files saved to fillers/")
    print("=" * 55)
    print()


if __name__ == "__main__":
    main()
