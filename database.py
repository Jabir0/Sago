# database.py
import sqlite3
import uuid
from datetime import datetime

DATABASE_NAME = "gizibot_history.db"

def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Table for chat sessions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT, -- Placeholder for future multi-user
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')

    # Table for chat messages
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()
    print(f"Database '{DATABASE_NAME}' initialized.")

def create_new_session(user_id="default_user", title="New Chat") -> str:
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    session_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO chat_sessions (id, user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (session_id, user_id, title, now, now)
    )
    conn.commit()
    conn.close()
    return session_id

def update_session_title(session_id: str, new_title: str):
    """Updates the title of a chat session."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute(
        "UPDATE chat_sessions SET title = ?, updated_at = ? WHERE id = ?",
        (new_title, now, session_id)
    )
    conn.commit()
    conn.close()
    print(f"Session {session_id} title updated to: {new_title}")


def get_session_by_id(session_id: str) -> dict:
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, title, created_at, updated_at FROM chat_sessions WHERE id = ?", (session_id,))
    session_data = cursor.fetchone()
    conn.close()
    if session_data:
        return {
            "id": session_data[0],
            "user_id": session_data[1],
            "title": session_data[2],
            "created_at": session_data[3],
            "updated_at": session_data[4]
        }
    return None

def get_all_sessions(user_id="default_user") -> list[dict]:
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row # Return rows as dict-like objects
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, created_at, updated_at FROM chat_sessions WHERE user_id = ? ORDER BY updated_at DESC", (user_id,))
    sessions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return sessions

def save_message(session_id: str, role: str, content: str, timestamp: datetime):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    iso_timestamp = timestamp.isoformat()
    cursor.execute(
        "INSERT INTO chat_messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
        (session_id, role, content, iso_timestamp)
    )
    # Update session's updated_at timestamp
    cursor.execute(
        "UPDATE chat_sessions SET updated_at = ? WHERE id = ?",
        (iso_timestamp, session_id)
    )
    conn.commit()
    conn.close()

def get_messages_for_session(session_id: str) -> list[dict]:
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT role, content, timestamp FROM chat_messages WHERE session_id = ? ORDER BY timestamp ASC", (session_id,))
    messages = []
    for row in cursor.fetchall():
        msg = dict(row)
        msg['timestamp'] = datetime.fromisoformat(msg['timestamp'])
        messages.append(msg)
    conn.close()
    return messages

def delete_session(session_id: str):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()

def delete_all_sessions(user_id="default_user"):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_sessions WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()