# ============================================================
# core/llm_engine.py — Gemma 3 conversation engine via LM Studio
# ============================================================
# Handles the conversation loop with the LLM:
# - Loads Maya's personality prompt
# - Maintains a sliding window of conversation history
# - Supports both regular and STREAMING responses
# - Streaming yields sentences as they're generated
# ============================================================

import os
import re
import json
import requests

import config
from utils import logger


# Sentence boundary pattern — split on . ! ? followed by space or end
SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+')


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

    def _build_messages(self, user_message: str) -> list[dict]:
        """Build the messages payload with system prompt + history."""
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.history)
        messages.append({"role": "user", "content": user_message})
        return messages

    def _update_history(self, user_message: str, reply: str):
        """Add messages to history and trim to sliding window."""
        self.history.append({"role": "user", "content": user_message})
        self.history.append({"role": "assistant", "content": reply})

        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def chat(self, user_message: str) -> str:
        """
        Send a user message to Gemma and get Maya's full response.
        (Used by text mode)
        """
        messages = self._build_messages(user_message)

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

        self._update_history(user_message, reply)
        return reply

    def chat_stream(self, user_message: str):
        """
        Stream Gemma's response sentence by sentence.

        Yields sentences as they're completed (on . ! ? boundaries).
        This lets TTS start on sentence 1 while Gemma generates sentence 2.

        Yields:
            str: Each complete sentence as it's generated
        """
        messages = self._build_messages(user_message)

        try:
            response = requests.post(
                config.LM_STUDIO_URL,
                json={
                    "model": config.LM_STUDIO_MODEL,
                    "messages": messages,
                    "temperature": config.LLM_TEMPERATURE,
                    "max_tokens": config.LLM_MAX_TOKENS,
                    "stream": True,
                },
                timeout=30,
                stream=True,
            )
            response.raise_for_status()

            buffer = ""
            full_reply = ""

            for line in response.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data: "):
                    continue

                data_str = line[6:]  # Remove "data: " prefix

                if data_str.strip() == "[DONE]":
                    break

                try:
                    data = json.loads(data_str)
                    delta = data["choices"][0].get("delta", {})
                    token = delta.get("content", "")
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue

                if not token:
                    continue

                buffer += token
                full_reply += token

                # Check if we have a complete sentence
                parts = SENTENCE_SPLIT.split(buffer)
                if len(parts) > 1:
                    # Yield all complete sentences, keep the remainder
                    for sentence in parts[:-1]:
                        sentence = sentence.strip()
                        if sentence:
                            yield sentence
                    buffer = parts[-1]

            # Yield any remaining text
            if buffer.strip():
                yield buffer.strip()

            # Update history with full response
            self._update_history(user_message, full_reply)

        except requests.ConnectionError:
            logger.error("LLM", "Cannot connect to LM Studio — is it running?")
            yield "[neutral] Hmm, I spaced out for a second... what were you saying?"
            self._update_history(user_message, "I spaced out...")

        except requests.Timeout:
            logger.error("LLM", "LM Studio request timed out")
            yield "[neutral] Sorry, I got distracted... say that again?"
            self._update_history(user_message, "I got distracted...")

        except Exception as e:
            logger.error("LLM", f"Stream error: {e}")
            yield "[neutral] Wait, I kinda blanked out there. What?"
            self._update_history(user_message, "I blanked out...")
