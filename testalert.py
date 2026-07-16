import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.normpath(os.path.join(BASE_DIR, "packets.db"))


def get_latest_row():
    """Fetch the most recent row from the packets table."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us access columns by name
    try:
        cur = conn.execute(
            "SELECT * FROM warnings ORDER BY id DESC LIMIT 1"
        )
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()