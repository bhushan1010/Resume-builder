import os
import time
import threading
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------
RPM_LIMIT = 15           # Gemini Flash free tier: 15 requests per minute
RPM_SAFE_LIMIT = 14      # Stay 1 below to handle race conditions / safety buffer
COOLDOWN_SECONDS = 65    # 60s minute window + 5s buffer
MINUTE_WINDOW = 60       # seconds
DAY_WINDOW = 86400       # seconds (24h)

# Max number of keys to look for in env vars (GEMINI_KEY_1 .. GEMINI_KEY_N)
MAX_KEYS = int(os.getenv("MAX_GEMINI_KEYS", "10"))


class GeminiKeyManager:
    def __init__(self, api_keys: List[str]):
        self.keys = []
        for key in api_keys:
            self.keys.append({
                "key": key,
                "key_suffix": key[-4:] if len(key) >= 4 else "????",  # for safe logging
                "requests_this_minute": 0,
                "requests_today": 0,
                "minute_reset_at": time.time() + MINUTE_WINDOW,
                "day_reset_at": time.time() + DAY_WINDOW,
                "cooling_until": 0,                # 0 = not cooling
                "exhausted_today": False
            })
        self.current_index = 0
        self.lock = threading.Lock()

        if not self.keys:
            logger.error(
                "❌ GeminiKeyManager initialized with NO keys! "
                "Set GEMINI_KEY_1, GEMINI_KEY_2, ... in your environment."
            )
        else:
            logger.info(f"✅ GeminiKeyManager initialized with {len(self.keys)} key(s)")

    def _reset_expired_counters(self, key_state: dict, now: float):
        """Reset minute/day counters if their windows have expired."""
        if now > key_state["minute_reset_at"]:
            key_state["requests_this_minute"] = 0
            key_state["minute_reset_at"] = now + MINUTE_WINDOW

        if now > key_state["day_reset_at"]:
            key_state["requests_today"] = 0
            key_state["exhausted_today"] = False
            key_state["day_reset_at"] = now + DAY_WINDOW

    def get_available_key(self) -> Optional[str]:
        if not self.keys:
            logger.error("❌ No API keys configured!")
            return None

        with self.lock:
            # Start from current_index and check all keys
            start_index = self.current_index
            while True:
                key_state = self.keys[self.current_index]
                now = time.time()

                self._reset_expired_counters(key_state, now)

                # Check if key is available
                if (key_state["cooling_until"] <= now and
                        key_state["requests_this_minute"] < RPM_SAFE_LIMIT and
                        not key_state["exhausted_today"]):
                    # Use this key
                    key_state["requests_this_minute"] += 1
                    key_state["requests_today"] += 1
                    # Advance current_index for next call (round-robin)
                    self.current_index = (self.current_index + 1) % len(self.keys)
                    return key_state["key"]

                # Move to next key
                self.current_index = (self.current_index + 1) % len(self.keys)
                # If we've checked all keys, stop
                if self.current_index == start_index:
                    break

            # No key available
            logger.warning(
                f"⚠️ All {len(self.keys)} Gemini key(s) are currently unavailable "
                "(rate-limited or daily-exhausted)."
            )
            return None

    def mark_rate_limited(self, key: str, cooldown_seconds: int = COOLDOWN_SECONDS):
        with self.lock:
            for key_state in self.keys:
                if key_state["key"] == key:
                    key_state["cooling_until"] = time.time() + cooldown_seconds
                    key_state["requests_this_minute"] = RPM_LIMIT  # force cooldown
                    logger.warning(
                        f"🚦 Key ...{key_state['key_suffix']} rate-limited. "
                        f"Cooling for {cooldown_seconds}s."
                    )
                    break

    def mark_daily_exhausted(self, key: str):
        with self.lock:
            for key_state in self.keys:
                if key_state["key"] == key:
                    key_state["exhausted_today"] = True
                    logger.warning(
                        f"📅 Key ...{key_state['key_suffix']} marked daily-exhausted."
                    )
                    break

    def get_status(self) -> List[Dict[str, Any]]:
        with self.lock:
            status_list = []
            now = time.time()
            for idx, key_state in enumerate(self.keys):
                # Actually reset expired counters (consistent with get_available_key)
                self._reset_expired_counters(key_state, now)

                is_cooling = key_state["cooling_until"] > now
                cooling_seconds_remaining = max(0, int(key_state["cooling_until"] - now))

                available = (
                    not is_cooling
                    and key_state["requests_this_minute"] < RPM_SAFE_LIMIT
                    and not key_state["exhausted_today"]
                )

                status_list.append({
                    "key_index": idx,
                    "key_suffix": f"...{key_state['key_suffix']}",
                    "requests_this_minute": key_state["requests_this_minute"],
                    "requests_today": key_state["requests_today"],
                    "is_cooling": is_cooling,
                    "cooling_seconds_remaining": cooling_seconds_remaining,
                    "exhausted_today": key_state["exhausted_today"],
                    "available": available
                })
            return status_list


# ---------------------------------------------------------------------------
# Load keys from environment
# ---------------------------------------------------------------------------
def load_gemini_keys() -> List[str]:
    keys = []
    for i in range(1, MAX_KEYS + 1):
        key = os.getenv(f"GEMINI_KEY_{i}")
        if key:
            # Strip whitespace and accidental quotes
            key = key.strip().strip('"').strip("'")
            if key:
                keys.append(key)

    if not keys:
        logger.warning(
            "⚠️ No Gemini API keys found! Set GEMINI_KEY_1, GEMINI_KEY_2, etc. "
            "in your environment variables."
        )
    else:
        logger.info(f"✅ Loaded {len(keys)} Gemini API key(s) from environment")

    return keys


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
key_manager = GeminiKeyManager(load_gemini_keys())