import os
import sys
from google import genai
from google.genai import types

# Real keys from .env top lines
keys = [
    "AIzaSyDeAKYRFNYWeD_E4VwxKYv5tFZBWYd7V2U",
    "AIzaSyCyy7fIgeBG7j2zc0H0Q-l2GS6ZILW-5C0",
    "AIzaSyBGabxAxz8dZpyy1yApqmEQutzJkL4gLRw",
    "AIzaSyAl8ZdGPM4mIgR0FBbO4RvU7M2mvZjEATw",
    "AIzaSyBjgRmRbHbkq3q2wUSWYm6Z4KZV2nU6kJk"
]

print("Testing each Gemini API key directly...")
for idx, key in enumerate(keys):
    suffix = key[-4:] if len(key) >= 4 else "????"
    print(f"\n--- Testing Key {idx+1} (suffix: ...{suffix}) ---")
    try:
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Say 'Key working!'"
        )
        print(f"✅ Success! Response: {response.text.strip()}")
    except Exception as e:
        print(f"❌ Failed! Error: {e}")
