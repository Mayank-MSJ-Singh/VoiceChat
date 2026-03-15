# ============================================================
# main.py — Maya AI Voice Companion: Full Pipeline
# ============================================================
# Runs the complete real-time voice pipeline:
#   Mic → STT → LLM → TTS → Speaker
# All components run as threads communicating via queues.
#
# Features:
#   - Interrupt handling: Maya stops talking when you speak
#   - Graceful shutdown via Ctrl+C
#   - Text-only mode via --text flag
#
# Usage:
#   python main.py          → Voice mode (full pipeline)
#   python main.py --text   → Text-only mode (CLI chat)
# ============================================================

import sys
import time
import threading
import queue

import config
from core.llm_engine import LLMEngine
from core.emotion_engine import parse_emotion
from core.filler_engine import FillerEngine
from utils import logger
from utils import queues


# ============================================================
# Worker: LLM conversation — streaming (Thread 3)
# ============================================================
def llm_worker(llm: LLMEngine, speech_queue: queue.Queue, filler, audio_out, stop_event: threading.Event):
    """
    Reads transcribed text from speech_queue.
    Streams LLM response sentence by sentence:
      - Filler plays immediately
      - First sentence → parse emotion → TTS
      - Each subsequent sentence → TTS (same emotion)
      - Playback thread plays them in order
    """
    logger.success("LLM", "Worker ready — waiting for speech input")

    while not stop_event.is_set():
        try:
            user_text = speech_queue.get(timeout=0.5)
        except queue.Empty:
            continue

        # --- INTERRUPT: If Maya is currently speaking, stop her ---
        if audio_out.is_active():
            logger.info("INTERRUPT", "User spoke — interrupting Maya!")
            audio_out.stop()
            _drain_queue(queues.llm_queue)
            _drain_queue(queues.playback_queue)

        logger.chat_user(user_text)

        # --- FILLER: Play immediately while LLM starts ---
        filler_path = filler.get_filler(user_text) if filler else None
        if filler_path:
            queues.playback_queue.put((filler_path, 0.8))

        # --- STREAM: Send each sentence to TTS as it's generated ---
        emotion = "neutral"
        is_first = True

        for sentence in llm.chat_stream(user_text):
            if stop_event.is_set():
                break

            # Parse emotion from the first sentence (tag is at the start)
            if is_first:
                clean_text, emotion = parse_emotion(sentence)
                is_first = False
            else:
                clean_text = sentence

            if clean_text.strip():
                logger.chat_maya(clean_text, emotion)

                # Push each sentence to TTS independently
                volume = config.EMOTION_VOLUME.get(emotion, 1.0)
                queues.llm_queue.put((clean_text, emotion, volume))


# ============================================================
# Worker: TTS synthesis (Thread 4)
# ============================================================
def tts_worker(stop_event: threading.Event):
    """
    Reads (text, emotion) from llm_queue,
    synthesizes speech, pushes audio path to playback_queue.
    """
    from core.tts_engine import TTSEngine

    tts = TTSEngine()
    logger.success("TTS", "Worker ready")

    while not stop_event.is_set():
        try:
            text, emotion, volume = queues.llm_queue.get(timeout=0.5)
        except queue.Empty:
            continue

        wav_path = tts.synthesize(text, emotion)
        if wav_path:
            queues.playback_queue.put((wav_path, volume))


# ============================================================
# Worker: Audio playback (Thread 5)
# ============================================================
def playback_worker(audio_out, stop_event: threading.Event):
    """
    Reads audio file paths from playback_queue,
    plays them through speakers.
    Uses shared audio_out for interrupt support.
    """
    logger.success("PLAY", "Worker ready")

    while not stop_event.is_set():
        try:
            wav_path, volume = queues.playback_queue.get(timeout=0.5)
        except queue.Empty:
            continue

        audio_out.play(wav_path, volume=volume)


# ============================================================
# Utility: Drain a queue
# ============================================================
def _drain_queue(q: queue.Queue):
    """Remove all items from a queue without blocking."""
    while True:
        try:
            q.get_nowait()
        except queue.Empty:
            break


# ============================================================
# Voice Mode: Full Pipeline
# ============================================================
def run_voice_pipeline():
    """
    Run the full real-time voice pipeline.
    All 5 worker threads communicate via queues.
    Interrupt: user speech during playback stops Maya and processes new input.
    """
    print()
    print("=" * 55)
    print("  🎙️  Maya — AI Voice Companion")
    print("=" * 55)
    print("  Speak naturally into your microphone.")
    print("  Maya will listen, think, and respond.")
    print("  Interrupt her anytime by speaking!")
    print("  Press Ctrl+C to stop.")
    print("=" * 55)
    print()

    logger.info("Main", "Initializing pipeline...")

    # Shared stop event for graceful shutdown
    stop_event = threading.Event()

    # Initialize LLM engine (needs to load before thread starts)
    llm = LLMEngine()

    # Import audio components
    from core.audio_listener import AudioListener
    from core.speech_to_text import SpeechToText
    from core.audio_output import AudioOutput
    from core.bgm_player import BGMPlayer

    # Shared audio output (for interrupt coordination)
    audio_out = AudioOutput()

    # Filler engine (instant mood-based fillers while TTS works)
    filler = FillerEngine()

    # Background music (loops continuously at low volume)
    bgm = BGMPlayer()

    # Initialize STT components
    listener = AudioListener(queues.audio_queue)
    stt = SpeechToText(queues.audio_queue, queues.speech_queue)

    # ---- Start BGM first (runs independently) ----
    bgm.start()

    # ---- Start all worker threads ----
    threads = []

    # Thread 1: Mic capture
    t1 = threading.Thread(target=listener.start, name="AudioCapture", daemon=True)
    threads.append(t1)

    # Thread 2: Speech-to-Text
    t2 = threading.Thread(target=stt.start, name="SpeechToText", daemon=True)
    threads.append(t2)

    # Thread 3: LLM conversation (with filler + interrupt support)
    t3 = threading.Thread(
        target=llm_worker, args=(llm, queues.speech_queue, filler, audio_out, stop_event),
        name="LLMConversation", daemon=True,
    )
    threads.append(t3)

    # Thread 4: TTS synthesis
    t4 = threading.Thread(
        target=tts_worker, args=(stop_event,),
        name="TTSSynthesis", daemon=True,
    )
    threads.append(t4)

    # Thread 5: Audio playback (with shared audio_out)
    t5 = threading.Thread(
        target=playback_worker, args=(audio_out, stop_event),
        name="AudioPlayback", daemon=True,
    )
    threads.append(t5)

    # Start all threads
    logger.info("Main", "Starting pipeline threads...")
    for t in threads:
        t.start()
        logger.info("Main", f"  Started: {t.name}")

    print()
    logger.success("Main", "🎙️  Maya is live! Start speaking...\n")

    # Main thread waits for Ctrl+C
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n")
        logger.info("Main", "Shutting down...")
        stop_event.set()
        bgm.stop()
        listener.stop()
        stt.stop()
        audio_out.stop()
        time.sleep(1)
        logger.success("Main", "Goodbye! 👋")


# ============================================================
# Text Mode: CLI Chat (Phase 1 preserved)
# ============================================================
def run_text_chat():
    """Text-only chat mode (no audio). Type messages, get replies."""
    print()
    print("=" * 55)
    print("  🎙️  Maya — AI Voice Companion (Text Mode)")
    print("=" * 55)
    print("  Type a message and press Enter to chat with Maya.")
    print("  Type 'quit' or 'exit' to end the conversation.")
    print("=" * 55)
    print()

    try:
        llm = LLMEngine()
        logger.success("Main", "Maya is ready! Start chatting.\n")
    except Exception as e:
        logger.error("Main", f"Failed to initialize: {e}")
        sys.exit(1)

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "bye"):
                print("\nMaya: [soft] Byeee... talk to you later, okay?\n")
                break

            time.sleep(config.THINKING_DELAY_MIN)

            raw_reply = llm.chat(user_input)
            clean_text, emotion = parse_emotion(raw_reply)
            logger.chat_maya(clean_text, emotion)

        except KeyboardInterrupt:
            print("\n\nMaya: [soft] Oh... okay, bye then!\n")
            break
        except Exception as e:
            logger.error("Main", f"Error: {e}")
            continue


# ============================================================
# Entry Point
# ============================================================
if __name__ == "__main__":
    if "--text" in sys.argv:
        run_text_chat()
    else:
        run_voice_pipeline()
