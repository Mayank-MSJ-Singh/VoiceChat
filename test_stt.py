# ============================================================
# test_stt.py — Phase 2 test: Microphone → Text
# ============================================================
# Run this to verify that speech recognition works.
# Speak into your microphone and see transcribed text.
# Press Ctrl+C to stop.
# ============================================================

import queue
import threading

from core.audio_listener import AudioListener
from core.speech_to_text import SpeechToText
from utils import logger


def main():
    print()
    print("=" * 55)
    print("  🎙️  Maya — Speech-to-Text Test")
    print("=" * 55)
    print("  Speak into your microphone.")
    print("  Transcribed text will appear below.")
    print("  Press Ctrl+C to stop.")
    print("=" * 55)
    print()

    # Create queues
    audio_queue = queue.Queue()
    speech_queue = queue.Queue()

    # Initialize components
    listener = AudioListener(audio_queue)
    stt = SpeechToText(audio_queue, speech_queue)

    # Start audio capture in a thread
    mic_thread = threading.Thread(target=listener.start, daemon=True)
    mic_thread.start()

    # Start STT in a thread
    stt_thread = threading.Thread(target=stt.start, daemon=True)
    stt_thread.start()

    # Main thread: print transcriptions
    try:
        while True:
            try:
                text = speech_queue.get(timeout=0.5)
                logger.chat_user(text)
            except queue.Empty:
                continue
    except KeyboardInterrupt:
        print("\n\nStopping...")
        listener.stop()
        stt.stop()
        print("Done!")


if __name__ == "__main__":
    main()
