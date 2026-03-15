# ============================================================
# core/thinking_delay.py — Human-like response delay
# ============================================================
# Adds a random pause before Maya responds, making conversation
# feel more natural and less robotic.
# ============================================================

import time
import random

import config
from utils import logger


def think():
    """
    Simulate human thinking time with a random delay.
    Range is configured in config.py (default: 1-2 seconds).
    """
    delay = random.uniform(config.THINKING_DELAY_MIN, config.THINKING_DELAY_MAX)
    logger.info("THINK", f"Thinking for {delay:.1f}s...")
    time.sleep(delay)
