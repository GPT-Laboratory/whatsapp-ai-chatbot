import sqlite3
from config import CONV_DB_PATH, MAX_MESSAGES

def init_db():
    """Initialize the SQLite database with a unique constraint."""
    # create folder if it doesn't exist

    conn = sqlite3.connect(CONV_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            message_content TEXT,
            timestamp INTEGER,
            from_me BOOLEAN,
            UNIQUE(user_id, message_content, timestamp, from_me)
        )
    """)
    conn.commit()
    conn.close()

def save_message(user_id, message_content, timestamp, from_me):
    """Insert a message into the DB if it doesn't already exist."""
    conn = sqlite3.connect(CONV_DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO messages (user_id, message_content, timestamp, from_me)
            VALUES (?, ?, ?, ?)
        """, (user_id, message_content, timestamp, from_me))
        conn.commit()
    except sqlite3.IntegrityError:
        # A message with the same (user_id, message_content, timestamp, from_me) already exists
        pass
    finally:
        conn.close()

def get_messages(user_id):
    """Retrieve all messages for a particular user_id."""
    conn = sqlite3.connect(CONV_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT message_content, timestamp, from_me
        FROM messages
        WHERE user_id = ?
        ORDER BY timestamp
    """, (user_id,))
    results = cursor.fetchall()
    conn.close()
    return results

def get_recent_messages(user_id):
    """
    Retrieve the most recent `max_messages` for a particular user_id, ordered oldest to newest.
    """
    conn = sqlite3.connect(CONV_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT message_content, timestamp, from_me
        FROM messages
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (user_id, MAX_MESSAGES))
    results = cursor.fetchall()
    conn.close()

    # Reverse the results to return them in chronological order
    return results[::-1]

def delete_messages(user_id):
    """Delete all messages for the specified user_id from the database."""
    conn = sqlite3.connect(CONV_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_recent_messages_formatted(user_id):
    # Build a minimal text representation of the conversation
    conversation_history = get_recent_messages(user_id)

    lines = []
    for msg_content, msg_timestamp, from_me in conversation_history:
        if from_me:
            speaker = "ASSISTANT"
        else:
            speaker = "USER"
        lines.append(f"{speaker}: {msg_content}")

    conversation_text = "\n".join(lines)

    return conversation_text