import sqlite3
from pathlib import Path

# Store the database in the project root, regardless of
# which directory you use to start the bot.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "socialpilot.db"


def get_connection():
    """Open a connection to the SQLite database."""
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    """Create the posts table when the application starts."""
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'draft',
                created_at TEXT NOT NULL DEFAULT (
                    strftime('%Y-%m-%d %H:%M:%S', 'now')
                ),
                published_at TEXT,
                channel_id TEXT
            )
        """)


def create_post(user_id: int, content: str) -> int:
    """Save a new post and return its database ID."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO posts (user_id, content)
            VALUES (?, ?)
            """,
            (user_id, content),
        )
        return cursor.lastrowid


def get_post(post_id: int, user_id: int):
    """Get one post belonging to a specific administrator."""
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT * FROM posts
            WHERE id = ? AND user_id = ?
            """,
            (post_id, user_id),
        ).fetchone()


def get_latest_draft(user_id: int):
    """Get the newest draft belonging to an administrator."""
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT * FROM posts
            WHERE user_id = ? AND status = 'draft'
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()


def get_recent_posts(user_id: int, limit: int = 10):
    """Return recent posts belonging to an administrator."""
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT * FROM posts
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()


def update_status(
    post_id: int,
    user_id: int,
    status: str,
    channel_id: str | None = None,
) -> bool:
    """Update a post status and optional publication details."""
    with get_connection() as connection:
        if status == "published":
            cursor = connection.execute(
                """
                UPDATE posts
                SET status = ?,
                    published_at = strftime('%Y-%m-%d %H:%M:%S', 'now'),
                    channel_id = ?
                WHERE id = ? AND user_id = ? AND status = 'publishing'
                """,
                (status, channel_id, post_id, user_id),
            )
        else:
            cursor = connection.execute(
                """
                UPDATE posts
                SET status = ?
                WHERE id = ? AND user_id = ?
                """,
                (status, post_id, user_id),
            )

        return cursor.rowcount > 0


def start_publishing(post_id: int, user_id: int) -> bool:
    """
    Reserve a draft for publishing.

    Only one request can change a draft from 'draft' to
    'publishing', helping prevent duplicate button clicks.
    """
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE posts
            SET status = 'publishing'
            WHERE id = ? AND user_id = ? AND status = 'draft'
            """,
            (post_id, user_id),
        )
        return cursor.rowcount > 0
