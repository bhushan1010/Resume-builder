"""
Database module for storing session information.
"""

def save_session(session_id: str, data: dict) -> bool:
    """Saves the session data to SQLite db."""
    # In a real app, this would execute SQL queries.
    print(f"Saving session {session_id} to database...")
    return True

def get_user_profile(user_id: str) -> dict:
    """Fetches user information from database."""
    return {"user_id": user_id, "name": "Test User"}
