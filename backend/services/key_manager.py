import os
import time
import threading
from typing import List, Dict, Any, Optional

from fastapi import HTTPException

class GeminiKeyManager:
    def __init__(self, api_keys: List[str]):
        self.keys = []
        for key in api_keys:
            self.keys.append({
                "key": key,
                "requests_this_minute": 0,
                "requests_today": 0,
                "minute_reset_at": time.time() + 60,  # reset in 60 seconds
                "day_reset_at": time.time() + 86400,   # reset in 24 hours
                "cooling_until": 0,                     # 0 = not cooling
                "exhausted_today": False
            })
        self.current_index = 0
        self.lock = threading.Lock()

    def get_available_key(self) -> Optional[str]:
        if not self.keys:
            return None
        with self.lock:
            # Start from current_index and check all keys
            start_index = self.current_index
            while True:
                key_state = self.keys[self.current_index]
                now = time.time()

                # Reset minute counter if time > minute_reset_at
                if now > key_state["minute_reset_at"]:
                    key_state["requests_this_minute"] = 0
                    key_state["minute_reset_at"] = now + 60

                # Reset day counter + exhausted_today if time > day_reset_at
                if now > key_state["day_reset_at"]:
                    key_state["requests_today"] = 0
                    key_state["exhausted_today"] = False
                    key_state["day_reset_at"] = now + 86400

                # Check if key is available
                if (key_state["cooling_until"] <= now and 
                    key_state["requests_this_minute"] < 14 and 
                    not key_state["exhausted_today"]):
                    # Use this key
                    key_state["requests_this_minute"] += 1
                    key_state["requests_today"] += 1
                    # Configure genai with this key (will be done by caller)
                    # Advance current_index for next call
                    self.current_index = (self.current_index + 1) % len(self.keys)
                    return key_state["key"]

                # Move to next key
                self.current_index = (self.current_index + 1) % len(self.keys)
                # If we've checked all keys, break
                if self.current_index == start_index:
                    break

            # No key available
            return None

    def mark_rate_limited(self, key: str, cooldown_seconds: int = 65):
        with self.lock:
            for key_state in self.keys:
                if key_state["key"] == key:
                    key_state["cooling_until"] = time.time() + cooldown_seconds
                    key_state["requests_this_minute"] = 15  # force cooldown
                    break

    def mark_daily_exhausted(self, key: str):
        with self.lock:
            for key_state in self.keys:
                if key_state["key"] == key:
                    key_state["exhausted_today"] = True
                    break

    def get_status(self) -> List[Dict[str, Any]]:
        with self.lock:
            status_list = []
            now = time.time()
            for idx, key_state in enumerate(self.keys):
                # Reset counters for status check (but don't save)
                minute_requests = key_state["requests_this_minute"]
                day_requests = key_state["requests_today"]
                if now > key_state["minute_reset_at"]:
                    minute_requests = 0
                if now > key_state["day_reset_at"]:
                    day_requests = 0
                    exhausted = False
                else:
                    exhausted = key_state["exhausted_today"]

                is_cooling = key_state["cooling_until"] > now
                cooling_seconds_remaining = max(0, int(key_state["cooling_until"] - now))

                available = (not is_cooling and 
                            minute_requests < 14 and 
                            not exhausted and 
                            not key_state["exhausted_today"])

                status_list.append({
                    "key_index": idx,
                    "requests_this_minute": minute_requests,
                    "requests_today": day_requests,
                    "is_cooling": is_cooling,
                    "cooling_seconds_remaining": cooling_seconds_remaining,
                    "exhausted_today": exhausted,
                    "available": available
                })
            return status_list

# Load keys from environment
def load_gemini_keys() -> List[str]:
    keys = []
    for i in range(1, 6):
        key = os.getenv(f"GEMINI_KEY_{i}")
        if key:
            keys.append(key)
    return keys

# Module-level singleton
key_manager = GeminiKeyManager(load_gemini_keys())