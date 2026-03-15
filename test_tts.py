# ============================================================
# test_tts.py — Phase 3 test: Text → Speech
# ============================================================
# Run this to verify that TTS works.
# Type text, hear Maya speak it back through your speakers.
# Press Ctrl+C to stop.
#
# IMPORTANT: You need at least one voice sample in voices/.
# Run generate_voice_sample.py first if you don't have one.
# ============================================================

import sys
import os

from core.tts_engine import TTSEngine
from core.audio_output import AudioOutput
from core.emotion_engine import parse_emotion
from utils import logger


def main():
    print()
    print("=" * 55)
    print("  🔊  Maya — Text-to-Speech Test")
    print("=" * 55)
    print("  Type text with [emotion] tags to hear Maya speak.")
    print("  Examples:")
    print("    [happy] Oh my god, that's amazing!")
    print("    [soft] Hey... you okay?")
    print("    [teasing] Oh really now?")
    print("    Hello, how are you?")
    print("  Type 'quit' to stop.")
    print("=" * 55)
    print()

    # Check for voice samples
    voices_dir = os.path.join(os.path.dirname(__file__), "voices")
    if not os.path.exists(voices_dir) or not any(f.endswith(".wav") for f in os.listdir(voices_dir)):
        print("ERROR: No voice samples found in voices/")
        print("Run 'python generate_voice_sample.py' first to create one.")
        sys.exit(1)

    # Initialize TTS and audio output
    tts = TTSEngine()
    audio = AudioOutput()

    while True:
        try:
            text = input("Say: ").strip()

            if not text:
                continue
            if text.lower() in ("quit", "exit"):
                break

            # Parse emotion if tagged
            clean_text, emotion = parse_emotion(text)

            # Synthesize speech
            wav_path = tts.synthesize(clean_text, emotion)

            if wav_path:
                # Play it
                audio.play(wav_path)

        except KeyboardInterrupt:
            print("\nDone!")
            break
        except Exception as e:
            logger.error("Test", f"Error: {e}")
            continue


if __name__ == "__main__":
    main()
