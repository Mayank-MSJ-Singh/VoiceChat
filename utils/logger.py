# ============================================================
# utils/logger.py — Simple colored logging for Maya
# ============================================================

import sys
from datetime import datetime


# ANSI color codes
COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
}


def _timestamp():
    return datetime.now().strftime("%H:%M:%S")


def info(module: str, message: str):
    """General info log — cyan"""
    print(f"{COLORS['dim']}{_timestamp()}{COLORS['reset']} {COLORS['cyan']}[{module}]{COLORS['reset']} {message}")


def success(module: str, message: str):
    """Success log — green"""
    print(f"{COLORS['dim']}{_timestamp()}{COLORS['reset']} {COLORS['green']}[{module}]{COLORS['reset']} {message}")


def warn(module: str, message: str):
    """Warning log — yellow"""
    print(f"{COLORS['dim']}{_timestamp()}{COLORS['reset']} {COLORS['yellow']}[{module}]{COLORS['reset']} {message}")


def error(module: str, message: str):
    """Error log — red"""
    print(f"{COLORS['dim']}{_timestamp()}{COLORS['reset']} {COLORS['red']}[{module}]{COLORS['reset']} {message}", file=sys.stderr)


def chat_user(text: str):
    """Display user message"""
    print(f"\n{COLORS['bold']}{COLORS['blue']}You:{COLORS['reset']} {text}")


def chat_maya(text: str, emotion: str = "neutral"):
    """Display Maya's response with emotion tag"""
    emotion_colors = {
        "happy": COLORS["green"],
        "soft": COLORS["magenta"],
        "teasing": COLORS["yellow"],
        "neutral": COLORS["cyan"],
    }
    color = emotion_colors.get(emotion, COLORS["cyan"])
    print(f"{COLORS['bold']}{color}Maya [{emotion}]:{COLORS['reset']} {text}\n")
