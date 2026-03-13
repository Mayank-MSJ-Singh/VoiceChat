# ============================================================
# main.py — Maya AI Voice Companion: Entry Point
# ============================================================
# Phase 1: Text-based CLI chat with Gemma 3 via LM Studio
# Future phases will add STT, TTS, and full voice pipeline.
# ============================================================

import sys
import time
import random

import config
from core.llm_engine import LLMEngine
from core.emotion_engine import parse_emotion
from utils import logger


def run_text_chat():
    """
    Phase 1: Interactive text chat with Maya.
    Type messages, get conversational replies with emotion tags.
    """
    print()
    print("=" * 55)
    print("  🎙️  Maya — AI Voice Companion (Text Mode)")
    print("=" * 55)
    print("  Type a message and press Enter to chat with Maya.")
    print("  Type 'quit' or 'exit' to end the conversation.")
    print("=" * 55)
    print()

    # Initialize the LLM engine
    try:
        llm = LLMEngine()
        logger.success("Main", "Maya is ready! Start chatting.\n")
    except Exception as e:
        logger.error("Main", f"Failed to initialize: {e}")
        sys.exit(1)

    # Chat loop
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "bye"):
                print("\nMaya: [soft] Byeee... talk to you later, okay?\n")
                break

            # Show what the user said (for future audio mode parity)
            # logger.chat_user(user_input)  # Uncomment when using mic input

            # Simulate thinking delay (makes it feel human)
            delay = random.uniform(config.THINKING_DELAY_MIN, config.THINKING_DELAY_MAX)
            time.sleep(delay)

            # Get response from Gemma
            raw_reply = llm.chat(user_input)

            # Parse emotion tag from response
            clean_text, emotion = parse_emotion(raw_reply)

            # Display Maya's response
            logger.chat_maya(clean_text, emotion)

        except KeyboardInterrupt:
            print("\n\nMaya: [soft] Oh... okay, bye then!\n")
            break
        except Exception as e:
            logger.error("Main", f"Error: {e}")
            continue


if __name__ == "__main__":
    run_text_chat()
