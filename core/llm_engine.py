# ============================================================
# core/llm_engine.py — Gemma 3 conversation engine via LM Studio
# ============================================================
# Handles the conversation loop with the LLM:
# - Loads Maya's personality prompt
# - Maintains a sliding window of conversation history
# - Sends requests to LM Studio's OpenAI-compatible API
# ============================================================

import os
import requests

import config
from utils import logger


class LLMEngine:
    """Manages conversation with Gemma 3 via LM Studio."""

    def __init__(self):
        # Load personality prompt from file
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            config.PERSONALITY_PROMPT_PATH,
        )
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.system_prompt = f.read().strip()

        # Conversation history — sliding window of last N messages
        self.history: list[dict[str, str]] = []
        self.max_history = config.CONVERSATION_HISTORY_LENGTH

        logger.info("LLM", f"Loaded personality prompt ({len(self.system_prompt)} chars)")
        logger.info("LLM", f"Target: {config.LM_STUDIO_URL}")

    def chat(self, user_message: str) -> str:
        """
        Send a user message to Gemma and get Maya's response.

        Args:
            user_message: The user's transcribed speech or typed text

        Returns:
            Raw LLM response (with emotion tag still included)
        """
        # Add user message to history
        self.history.append({"role": "user", "content": user_message})

        # Build the messages payload
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.history)

        # Send request to LM Studio
        try:
            response = requests.post(
                config.LM_STUDIO_URL,
                json={
                    "model": config.LM_STUDIO_MODEL,
                    "messages": messages,
                    "temperature": config.LLM_TEMPERATURE,
                    "max_tokens": config.LLM_MAX_TOKENS,
                },
                timeout=30,
            )
            response.raise_for_status()

            reply = response.json()["choices"][0]["message"]["content"].strip()

        except requests.ConnectionError:
            logger.error("LLM", "Cannot connect to LM Studio — is it running?")
            reply = "[neutral] Hmm, I spaced out for a second... what were you saying?"

        except requests.Timeout:
            logger.error("LLM", "LM Studio request timed out")
            reply = "[neutral] Sorry, I got distracted... say that again?"

        except Exception as e:
            logger.error("LLM", f"Unexpected error: {e}")
            reply = "[neutral] Wait, I kinda blanked out there. What?"

        # Add assistant reply to history
        self.history.append({"role": "assistant", "content": reply})

        # Trim history to sliding window
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

        return reply
