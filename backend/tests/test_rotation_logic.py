import os
import sys
import logging
from dotenv import load_dotenv

# Add backend directory to sys.path so we can import services
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

# Set logging to see warning logs of rotation
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

# Ensure we load correct env
# Load from root directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(PROJECT_ROOT), '.env'))
# Also fallback/load from backend directory if present
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, '.env'))

from services.key_manager import key_manager
from services.gemini import call_gemini_with_retry

print("Loaded keys from key manager:")
for idx, k in enumerate(key_manager.keys):
    print(f"Key {idx + 1}: suffix={k['key_suffix']}, requests_this_minute={k['requests_this_minute']}, exhausted_today={k['exhausted_today']}")

print("\nCalling call_gemini_with_retry to test key rotation...")
try:
    response = call_gemini_with_retry(
        prompt_content="Say 'Rotation working!'"
    )
    print(f"\n✅ SUCCESS! Response: {response.text.strip()}")
except Exception as e:
    print(f"\n❌ FAILED! Error: {e}")
    sys.exit(1)

print("\nKey manager state after call:")
for idx, k in enumerate(key_manager.keys):
    print(f"Key {idx + 1}: suffix={k['key_suffix']}, requests_this_minute={k['requests_this_minute']}, exhausted_today={k['exhausted_today']}")
