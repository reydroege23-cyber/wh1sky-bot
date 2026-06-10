"""Production moderation and group-management services.

This module intentionally plugs into the current monolithic bot while providing
the durable foundation needed for a cleaner modular architecture.
"""

from __future__ import annotations

import json
import shutil
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


DB_PATH = Path("data/group_management.db")
BACKUP_DIR = Path("data/backups")


DEFAULT_SETTINGS = {
    "guardian": False,
    "antispam": True,
    "antilink": False,
    "antiflood": True,
    "antiemoji": False,
    "antiraid": True,
    "captcha": False,
    "ai_enabled": True,
    "aireplies": True,
    "aimode": "normal",
    "ai_cooldown": 10,
    "speak_mode": False,
    "welcome_enabled": False,
    "goodbye_enabled": False,
    "slowmode": 0,
    "spam_threshold": 5,
    "flood_window": 10,
    "raid_join_threshold": 8,
    "raid_window": 60,
    "warnings_limit": 3,
    "punishment": "mute",
    "log_channel": "",
    "group_language": "en",
    "maintenance": False,
    "command_permissions": "{}",
    "silent_permission_mode": True,
    "rules": "No rules have been set yet.",
    "welcome": "Welcome {mention} to {chat}!",
    "goodbye": "Goodbye {name}.",
}


SETTING_COLUMNS: dict[str, tuple[str, str]] = {
    "antispam": ("antispam_enabled", "bool"),
    "antilink": ("antilink_enabled", "bool"),
    "antiflood": ("antiflood_enabled", "bool"),
    "antiemoji": ("antiemoji_enabled", "bool"),
    "antiraid": ("antiraid_enabled", "bool"),
    "guardian": ("guardian_enabled", "bool"),
    "captcha": ("captcha_enabled", "bool"),
    "ai_enabled": ("ai_enabled", "bool"),
    "aireplies": ("aireplies_enabled", "bool"),
    "aimode": ("aimode", "text"),
    "ai_cooldown": ("ai_cooldown", "int"),
    "speak_mode": ("speak_mode_enabled", "bool"),
    "welcome_enabled": ("welcome_enabled", "bool"),
    "goodbye_enabled": ("goodbye_enabled", "bool"),
    "maintenance": ("maintenance_enabled", "bool"),
    "rules": ("rules", "text"),
    "welcome": ("welcome_message", "text"),
    "goodbye": ("goodbye_message", "text"),
    "warnings_limit": ("warning_limit", "int"),
    "punishment": ("punishment_type", "text"),
    "log_channel": ("log_chat_id", "nullable_int"),
    "group_language": ("group_language", "text"),
    "command_permissions": ("command_permissions", "text"),
    "silent_permission_mode": ("silent_permission_mode", "bool"),
    "slowmode": ("slowmode", "int"),
    "spam_threshold": ("spam_threshold", "int"),
    "flood_window": ("flood_window", "int"),
    "raid_join_threshold": ("raid_join_threshold", "int"),
    "raid_window": ("raid_window", "int"),
}


CHAT_SETTINGS_COLUMNS_SQL = {
    "antispam_enabled": "INTEGER NOT NULL DEFAULT 1",
    "antilink_enabled": "INTEGER NOT NULL DEFAULT 0",
    "antiflood_enabled": "INTEGER NOT NULL DEFAULT 1",
    "antiemoji_enabled": "INTEGER NOT NULL DEFAULT 0",
    "antiraid_enabled": "INTEGER NOT NULL DEFAULT 1",
    "guardian_enabled": "INTEGER NOT NULL DEFAULT 0",
    "captcha_enabled": "INTEGER NOT NULL DEFAULT 0",
    "ai_enabled": "INTEGER NOT NULL DEFAULT 1",
    "aireplies_enabled": "INTEGER NOT NULL DEFAULT 1",
    "aimode": "TEXT NOT NULL DEFAULT 'normal'",
    "ai_cooldown": "INTEGER NOT NULL DEFAULT 10",
    "speak_mode_enabled": "INTEGER NOT NULL DEFAULT 0",
    "welcome_enabled": "INTEGER NOT NULL DEFAULT 0",
    "goodbye_enabled": "INTEGER NOT NULL DEFAULT 0",
    "maintenance_enabled": "INTEGER NOT NULL DEFAULT 0",
    "rules": "TEXT NOT NULL DEFAULT 'No rules have been set yet.'",
    "welcome_message": "TEXT NOT NULL DEFAULT 'Welcome {mention} to {chat}!'",
    "goodbye_message": "TEXT NOT NULL DEFAULT 'Goodbye {name}.'",
    "warning_limit": "INTEGER NOT NULL DEFAULT 3",
    "punishment_type": "TEXT NOT NULL DEFAULT 'mute'",
    "log_chat_id": "INTEGER DEFAULT NULL",
    "group_language": "TEXT NOT NULL DEFAULT 'en'",
    "command_permissions": "TEXT NOT NULL DEFAULT '{}'",
    "silent_permission_mode": "INTEGER NOT NULL DEFAULT 1",
    "slowmode": "INTEGER NOT NULL DEFAULT 0",
    "spam_threshold": "INTEGER NOT NULL DEFAULT 5",
    "flood_window": "INTEGER NOT NULL DEFAULT 10",
    "raid_join_threshold": "INTEGER NOT NULL DEFAULT 8",
    "raid_window": "INTEGER NOT NULL DEFAULT 60",
}


@dataclass(frozen=True)
class TargetUser:
    user_id: int
    display_name: str
    username: str | None = None


class GroupStore:
    """SQLite store for moderation logs, settings, reports, and analytics."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        self.init_schema()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS mod_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    actor_id INTEGER,
                    target_id INTEGER,
                    action TEXT NOT NULL,
                    reason TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_mod_logs_chat_created
                    ON mod_logs(chat_id, created_at DESC);

                CREATE TABLE IF NOT EXISTS permanent_bans (
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    reason TEXT,
                    created_by INTEGER,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY(chat_id, user_id)
                );

                CREATE TABLE IF NOT EXISTS message_stats (
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    message_count INTEGER NOT NULL DEFAULT 0,
                    last_seen TEXT NOT NULL,
                    PRIMARY KEY(chat_id, user_id)
                );

                CREATE TABLE IF NOT EXISTS known_users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    username_norm TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    full_name TEXT,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_known_users_username_norm
                    ON known_users(username_norm);

                CREATE TABLE IF NOT EXISTS chat_members_seen (
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    username_norm TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    full_name TEXT,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    message_count INTEGER NOT NULL DEFAULT 0,
                    warnings INTEGER NOT NULL DEFAULT 0,
                    bans INTEGER NOT NULL DEFAULT 0,
                    reputation INTEGER NOT NULL DEFAULT 100,
                    PRIMARY KEY(chat_id, user_id)
                );
                CREATE INDEX IF NOT EXISTS idx_chat_members_seen_username
                    ON chat_members_seen(chat_id, username_norm);

                CREATE TABLE IF NOT EXISTS warnings (
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    warning_count INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY(chat_id, user_id)
                );

                CREATE TABLE IF NOT EXISTS mutes (
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    until_at TEXT,
                    reason TEXT,
                    created_by INTEGER,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY(chat_id, user_id)
                );

                CREATE TABLE IF NOT EXISTS bans (
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    reason TEXT,
                    created_by INTEGER,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY(chat_id, user_id)
                );

                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    reporter_id INTEGER NOT NULL,
                    target_id INTEGER,
                    reason TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS security_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER,
                    event_type TEXT NOT NULL,
                    detail TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS notes (
                    chat_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    value TEXT NOT NULL,
                    created_by INTEGER,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY(chat_id, name)
                );

                CREATE TABLE IF NOT EXISTS rules (
                    chat_id INTEGER PRIMARY KEY,
                    text TEXT NOT NULL,
                    updated_by INTEGER,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS welcome_messages (
                    chat_id INTEGER PRIMARY KEY,
                    text TEXT NOT NULL,
                    updated_by INTEGER,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS goodbye_messages (
                    chat_id INTEGER PRIMARY KEY,
                    text TEXT NOT NULL,
                    updated_by INTEGER,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS ai_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_ai_memory_chat_user
                    ON ai_memory(chat_id, user_id, created_at DESC);

                CREATE TABLE IF NOT EXISTS command_usage_stats (
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER,
                    command TEXT NOT NULL,
                    count INTEGER NOT NULL DEFAULT 0,
                    last_used TEXT NOT NULL,
                    PRIMARY KEY(chat_id, user_id, command)
                );

                CREATE TABLE IF NOT EXISTS admin_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    admin_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    target_id INTEGER,
                    detail TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS captcha_verification (
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    challenge TEXT,
                    expires_at TEXT,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY(chat_id, user_id)
                );

                CREATE TABLE IF NOT EXISTS invite_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    invite_link TEXT,
                    inviter_id INTEGER,
                    joined_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS whitelist (
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    added_by INTEGER,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY(chat_id, user_id)
                );

                CREATE TABLE IF NOT EXISTS bot_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_by INTEGER,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS chat_registry (
                    chat_id INTEGER PRIMARY KEY,
                    title TEXT,
                    chat_type TEXT,
                    username TEXT,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL
                );
                """
            )
            self._migrate_chat_settings(conn)

    def _migrate_chat_settings(self, conn: sqlite3.Connection) -> None:
        """Create the per-chat settings table and migrate legacy key/value rows."""
        columns = conn.execute("PRAGMA table_info(chat_settings)").fetchall()
        names = {row["name"] for row in columns}

        if "key" in names and "value" in names:
            legacy_name = "chat_settings_kv"
            existing = conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
                (legacy_name,),
            ).fetchone()
            if existing:
                stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
                legacy_name = f"chat_settings_kv_{stamp}"
            conn.execute(f"ALTER TABLE chat_settings RENAME TO {legacy_name}")
            self._create_chat_settings_table(conn)
            rows = conn.execute(f"SELECT chat_id, key, value FROM {legacy_name}").fetchall()
            for row in rows:
                if row["key"] not in SETTING_COLUMNS:
                    continue
                try:
                    value = json.loads(row["value"])
                except json.JSONDecodeError:
                    value = row["value"]
                self._set_setting_conn(conn, int(row["chat_id"]), row["key"], value)
            return

        self._create_chat_settings_table(conn)
        current_columns = {row["name"] for row in conn.execute("PRAGMA table_info(chat_settings)").fetchall()}
        for column, column_sql in CHAT_SETTINGS_COLUMNS_SQL.items():
            if column not in current_columns:
                conn.execute(f"ALTER TABLE chat_settings ADD COLUMN {column} {column_sql}")
        if "updated_at" not in current_columns:
            conn.execute("ALTER TABLE chat_settings ADD COLUMN updated_at TEXT")

    @staticmethod
    def _create_chat_settings_table(conn: sqlite3.Connection) -> None:
        extra_columns = ",\n                    ".join(
            f"{column} {definition}" for column, definition in CHAT_SETTINGS_COLUMNS_SQL.items()
        )
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS chat_settings (
                chat_id INTEGER PRIMARY KEY,
                {extra_columns},
                updated_at TEXT NOT NULL
            )
            """
        )

    @staticmethod
    def now() -> str:
        return datetime.utcnow().isoformat(timespec="seconds")

    def log_action(
        self,
        chat_id: int,
        actor_id: int | None,
        action: str,
        target_id: int | None = None,
        reason: str | None = None,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO mod_logs(chat_id, actor_id, target_id, action, reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (chat_id, actor_id, target_id, action, reason, self.now()),
            )

    def record_user(self, chat_id: int, user: Any, increment_messages: bool = False) -> None:
        user_id = int(getattr(user, "id"))
        username = getattr(user, "username", None) or ""
        username_norm = username.lower().lstrip("@") if username else None
        first_name = getattr(user, "first_name", None) or ""
        last_name = getattr(user, "last_name", None) or ""
        full_name = getattr(user, "full_name", None) or " ".join(part for part in [first_name, last_name] if part) or username or str(user_id)
        now = self.now()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO known_users(user_id, username, username_norm, first_name, last_name, full_name, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    username_norm = excluded.username_norm,
                    first_name = excluded.first_name,
                    last_name = excluded.last_name,
                    full_name = excluded.full_name,
                    last_seen = excluded.last_seen
                """,
                (user_id, username or None, username_norm, first_name, last_name, full_name, now, now),
            )
            conn.execute(
                """
                INSERT INTO chat_members_seen(
                    chat_id, user_id, username, username_norm, first_name, last_name,
                    full_name, first_seen, last_seen, message_count
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(chat_id, user_id) DO UPDATE SET
                    username = excluded.username,
                    username_norm = excluded.username_norm,
                    first_name = excluded.first_name,
                    last_name = excluded.last_name,
                    full_name = excluded.full_name,
                    last_seen = excluded.last_seen,
                    message_count = chat_members_seen.message_count + excluded.message_count
                """,
                (chat_id, user_id, username or None, username_norm, first_name, last_name, full_name, now, now, 1 if increment_messages else 0),
            )

    def record_command_usage(self, chat_id: int, user_id: int | None, command: str) -> None:
        now = self.now()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO command_usage_stats(chat_id, user_id, command, count, last_used)
                VALUES (?, ?, ?, 1, ?)
                ON CONFLICT(chat_id, user_id, command) DO UPDATE SET
                    count = count + 1,
                    last_used = excluded.last_used
                """,
                (chat_id, user_id, command.lower().lstrip("/"), now),
            )

    def resolve_known_user(self, chat_id: int, username: str) -> TargetUser | None:
        username_norm = username.lower().lstrip("@")
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT user_id, full_name, username
                FROM chat_members_seen
                WHERE chat_id = ? AND username_norm = ?
                ORDER BY last_seen DESC
                LIMIT 1
                """,
                (chat_id, username_norm),
            ).fetchone()
            if not row:
                row = conn.execute(
                    """
                    SELECT user_id, full_name, username
                    FROM known_users
                    WHERE username_norm = ?
                    ORDER BY last_seen DESC
                    LIMIT 1
                    """,
                    (username_norm,),
                ).fetchone()
        if not row:
            return None
        display = row["full_name"] or (f"@{row['username']}" if row["username"] else str(row["user_id"]))
        return TargetUser(int(row["user_id"]), display, row["username"])

    def known_users(self, chat_id: int, limit: int = 20) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return conn.execute(
                """
                SELECT user_id, username, full_name, last_seen, message_count
                FROM chat_members_seen
                WHERE chat_id = ?
                ORDER BY last_seen DESC
                LIMIT ?
                """,
                (chat_id, limit),
            ).fetchall()

    def search_users(self, chat_id: int, query: str, limit: int = 10) -> list[sqlite3.Row]:
        needle = f"%{query.lower().lstrip('@')}%"
        with self.connect() as conn:
            return conn.execute(
                """
                SELECT user_id, username, full_name, last_seen, message_count
                FROM chat_members_seen
                WHERE chat_id = ? AND (
                    username_norm LIKE ? OR lower(full_name) LIKE ? OR CAST(user_id AS TEXT) LIKE ?
                )
                ORDER BY last_seen DESC
                LIMIT ?
                """,
                (chat_id, needle, needle, needle, limit),
            ).fetchall()

    def record_invite_join(
        self,
        chat_id: int,
        user_id: int,
        invite_link: str | None = None,
        inviter_id: int | None = None,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO invite_tracking(chat_id, user_id, invite_link, inviter_id, joined_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (chat_id, user_id, invite_link, inviter_id, self.now()),
            )

    def register_chat(self, chat: Any) -> None:
        chat_id = int(getattr(chat, "id"))
        title = getattr(chat, "title", None) or getattr(chat, "full_name", None) or getattr(chat, "first_name", None) or str(chat_id)
        chat_type = getattr(chat, "type", None) or "unknown"
        username = getattr(chat, "username", None)
        now = self.now()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO chat_registry(chat_id, title, chat_type, username, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(chat_id) DO UPDATE SET
                    title = excluded.title,
                    chat_type = excluded.chat_type,
                    username = excluded.username,
                    last_seen = excluded.last_seen
                """,
                (chat_id, title, chat_type, username, now, now),
            )

    def registered_chats(self, include_private: bool = False, limit: int = 50) -> list[sqlite3.Row]:
        where = "" if include_private else "WHERE chat_type != 'private'"
        with self.connect() as conn:
            return conn.execute(
                f"SELECT * FROM chat_registry {where} ORDER BY last_seen DESC LIMIT ?",
                (limit,),
            ).fetchall()

    def set_bot_setting(self, key: str, value: Any, actor_id: int | None = None) -> None:
        payload = json.dumps(value, ensure_ascii=False)
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO bot_settings(key, value, updated_by, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_by = excluded.updated_by,
                    updated_at = excluded.updated_at
                """,
                (key, payload, actor_id, self.now()),
            )

    def get_bot_setting(self, key: str, default: Any = None) -> Any:
        with self.connect() as conn:
            row = conn.execute("SELECT value FROM bot_settings WHERE key = ?", (key,)).fetchone()
        if not row:
            return default
        try:
            return json.loads(row["value"])
        except json.JSONDecodeError:
            return row["value"]

    def all_bot_settings(self) -> dict[str, Any]:
        with self.connect() as conn:
            rows = conn.execute("SELECT key, value FROM bot_settings ORDER BY key").fetchall()
        result: dict[str, Any] = {}
        for row in rows:
            try:
                result[row["key"]] = json.loads(row["value"])
            except json.JSONDecodeError:
                result[row["key"]] = row["value"]
        return result

    def log_admin_action(
        self,
        chat_id: int,
        admin_id: int,
        action: str,
        target_id: int | None = None,
        detail: str = "",
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO admin_actions(chat_id, admin_id, action, target_id, detail, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (chat_id, admin_id, action, target_id, detail, self.now()),
            )
        self.log_action(chat_id, admin_id, action, target_id, detail)

    def recent_logs(self, chat_id: int, limit: int = 10) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return conn.execute(
                "SELECT * FROM mod_logs WHERE chat_id = ? ORDER BY id DESC LIMIT ?",
                (chat_id, limit),
            ).fetchall()

    def set_setting(self, chat_id: int, key: str, value: Any) -> None:
        with self.connect() as conn:
            self._set_setting_conn(conn, chat_id, key, value)

    def _ensure_settings_row(self, conn: sqlite3.Connection, chat_id: int) -> None:
        conn.execute(
            "INSERT OR IGNORE INTO chat_settings(chat_id, updated_at) VALUES (?, ?)",
            (chat_id, self.now()),
        )

    def _set_setting_conn(self, conn: sqlite3.Connection, chat_id: int, key: str, value: Any) -> None:
        if key not in SETTING_COLUMNS:
            raise KeyError(f"Unknown chat setting: {key}")
        column, value_type = SETTING_COLUMNS[key]
        self._ensure_settings_row(conn, chat_id)
        conn.execute(
            f"UPDATE chat_settings SET {column} = ?, updated_at = ? WHERE chat_id = ?",
            (self._encode_setting(value, value_type), self.now(), chat_id),
        )

    def get_setting(self, chat_id: int, key: str, default: Any = None) -> Any:
        if default is None:
            default = DEFAULT_SETTINGS.get(key)
        if key not in SETTING_COLUMNS:
            return default
        column, value_type = SETTING_COLUMNS[key]
        with self.connect() as conn:
            row = conn.execute(
                f"SELECT {column} AS value FROM chat_settings WHERE chat_id = ?",
                (chat_id,),
            ).fetchone()
        return self._decode_setting(row["value"], value_type, default) if row else default

    def all_settings(self, chat_id: int) -> dict[str, Any]:
        settings = dict(DEFAULT_SETTINGS)
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM chat_settings WHERE chat_id = ?", (chat_id,)).fetchone()
        if not row:
            return settings
        for key, (column, value_type) in SETTING_COLUMNS.items():
            settings[key] = self._decode_setting(row[column], value_type, DEFAULT_SETTINGS.get(key))
        return settings

    def reset_settings(self, chat_id: int) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM chat_settings WHERE chat_id = ?", (chat_id,))
            self._ensure_settings_row(conn, chat_id)

    def export_settings(self, chat_id: int) -> dict[str, Any]:
        return self.all_settings(chat_id)

    def import_settings(self, chat_id: int, settings: dict[str, Any]) -> None:
        with self.connect() as conn:
            self._ensure_settings_row(conn, chat_id)
            for key, value in settings.items():
                if key in SETTING_COLUMNS:
                    self._set_setting_conn(conn, chat_id, key, value)

    def copy_settings(self, source_chat_id: int, target_chat_id: int) -> None:
        self.import_settings(target_chat_id, self.export_settings(source_chat_id))

    @staticmethod
    def _encode_setting(value: Any, value_type: str) -> Any:
        if value_type == "bool":
            return 1 if bool(value) else 0
        if value_type == "int":
            return int(value)
        if value_type == "nullable_int":
            if value in {None, "", "none", "off"}:
                return None
            return int(value)
        return str(value)

    @staticmethod
    def _decode_setting(value: Any, value_type: str, default: Any = None) -> Any:
        if value is None:
            return default
        if value_type == "bool":
            return bool(value)
        if value_type == "int":
            return int(value)
        if value_type == "nullable_int":
            return "" if value is None else str(value)
        return value

    def add_permanent_ban(self, chat_id: int, user_id: int, reason: str, created_by: int) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO permanent_bans(chat_id, user_id, reason, created_by, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (chat_id, user_id, reason, created_by, self.now()),
            )
        self.log_action(chat_id, created_by, "permanent_ban", user_id, reason)

    def remove_permanent_ban(self, chat_id: int, user_id: int, actor_id: int) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM permanent_bans WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
        self.log_action(chat_id, actor_id, "permanent_unban", user_id)

    def is_permanently_banned(self, chat_id: int, user_id: int) -> bool:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM permanent_bans WHERE chat_id = ? AND user_id = ?",
                (chat_id, user_id),
            ).fetchone()
        return row is not None

    def permanent_bans(self, chat_id: int, limit: int = 50) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return conn.execute(
                "SELECT * FROM permanent_bans WHERE chat_id = ? ORDER BY created_at DESC LIMIT ?",
                (chat_id, limit),
            ).fetchall()

    def record_message(self, chat_id: int, user_id: int) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO message_stats(chat_id, user_id, message_count, last_seen)
                VALUES (?, ?, 1, ?)
                ON CONFLICT(chat_id, user_id) DO UPDATE SET
                    message_count = message_count + 1,
                    last_seen = excluded.last_seen
                """,
                (chat_id, user_id, self.now()),
            )

    def add_whitelist(self, chat_id: int, user_id: int, actor_id: int) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO whitelist(chat_id, user_id, added_by, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (chat_id, user_id, actor_id, self.now()),
            )
        self.log_action(chat_id, actor_id, "whitelist", user_id)

    def remove_whitelist(self, chat_id: int, user_id: int, actor_id: int) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM whitelist WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
        self.log_action(chat_id, actor_id, "unwhitelist", user_id)

    def is_whitelisted(self, chat_id: int, user_id: int) -> bool:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM whitelist WHERE chat_id = ? AND user_id = ?",
                (chat_id, user_id),
            ).fetchone()
        return row is not None

    def add_warning(self, chat_id: int, user_id: int) -> int:
        with self.connect() as conn:
            self._ensure_settings_row(conn, chat_id)
            conn.execute(
                """
                INSERT INTO warnings(chat_id, user_id, warning_count, updated_at)
                VALUES (?, ?, 1, ?)
                ON CONFLICT(chat_id, user_id) DO UPDATE SET
                    warning_count = warning_count + 1,
                    updated_at = excluded.updated_at
                """,
                (chat_id, user_id, self.now()),
            )
            row = conn.execute(
                "SELECT warning_count FROM warnings WHERE chat_id = ? AND user_id = ?",
                (chat_id, user_id),
            ).fetchone()
        return int(row["warning_count"])

    def get_warnings(self, chat_id: int, user_id: int) -> int:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT warning_count FROM warnings WHERE chat_id = ? AND user_id = ?",
                (chat_id, user_id),
            ).fetchone()
        return int(row["warning_count"]) if row else 0

    def clear_warnings(self, chat_id: int, user_id: int) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM warnings WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))

    def top_active(self, chat_id: int, limit: int = 10) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return conn.execute(
                "SELECT * FROM message_stats WHERE chat_id = ? ORDER BY message_count DESC LIMIT ?",
                (chat_id, limit),
            ).fetchall()

    def inactive(self, chat_id: int, days: int = 30, limit: int = 10) -> list[sqlite3.Row]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat(timespec="seconds")
        with self.connect() as conn:
            return conn.execute(
                """
                SELECT * FROM message_stats
                WHERE chat_id = ? AND last_seen < ?
                ORDER BY last_seen ASC LIMIT ?
                """,
                (chat_id, cutoff, limit),
            ).fetchall()

    def add_report(self, chat_id: int, reporter_id: int, target_id: int | None, reason: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO reports(chat_id, reporter_id, target_id, reason, created_at) VALUES (?, ?, ?, ?, ?)",
                (chat_id, reporter_id, target_id, reason, self.now()),
            )
        self.log_action(chat_id, reporter_id, "report", target_id, reason)

    def log_security_event(self, chat_id: int, event_type: str, user_id: int | None = None, detail: str = "") -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO security_events(chat_id, user_id, event_type, detail, created_at) VALUES (?, ?, ?, ?, ?)",
                (chat_id, user_id, event_type, detail, self.now()),
            )

    def security_counts(self, chat_id: int, minutes: int = 60) -> dict[str, int]:
        cutoff = (datetime.utcnow() - timedelta(minutes=minutes)).isoformat(timespec="seconds")
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT event_type, COUNT(*) AS count
                FROM security_events
                WHERE chat_id = ? AND created_at >= ?
                GROUP BY event_type
                """,
                (chat_id, cutoff),
            ).fetchall()
        return {row["event_type"]: row["count"] for row in rows}

    def save_note(self, chat_id: int, name: str, value: str, actor_id: int) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO notes(chat_id, name, value, created_by, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(chat_id, name) DO UPDATE SET
                    value = excluded.value,
                    created_by = excluded.created_by,
                    updated_at = excluded.updated_at
                """,
                (chat_id, name.lower(), value, actor_id, self.now()),
            )

    def get_note(self, chat_id: int, name: str) -> str | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT value FROM notes WHERE chat_id = ? AND name = ?",
                (chat_id, name.lower()),
            ).fetchone()
        return row["value"] if row else None

    def delete_note(self, chat_id: int, name: str) -> bool:
        with self.connect() as conn:
            cur = conn.execute("DELETE FROM notes WHERE chat_id = ? AND name = ?", (chat_id, name.lower()))
            return cur.rowcount > 0

    def list_notes(self, chat_id: int) -> list[str]:
        with self.connect() as conn:
            rows = conn.execute("SELECT name FROM notes WHERE chat_id = ? ORDER BY name", (chat_id,)).fetchall()
        return [row["name"] for row in rows]

    def backup(self) -> Path:
        stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        dest = BACKUP_DIR / f"group_management-{stamp}.db"
        shutil.copy2(self.db_path, dest)
        return dest


class SecurityService:
    """In-memory fast checks backed by durable incident logs."""

    def __init__(self, store: GroupStore) -> None:
        self.store = store
        self.messages: dict[tuple[int, int], list[tuple[float, str]]] = {}
        self.joins: dict[int, list[float]] = {}

    def record_join(self, chat_id: int, user_id: int) -> str | None:
        if not self.store.get_setting(chat_id, "antiraid", True):
            return None
        now = time.time()
        joins = self.joins.setdefault(chat_id, [])
        joins.append(now)
        joins[:] = [stamp for stamp in joins if now - stamp <= 60]
        threshold = int(self.store.get_setting(chat_id, "raid_join_threshold", 8))
        if len(joins) >= threshold:
            self.store.log_security_event(chat_id, "raid", user_id, f"{len(joins)} joins in 60s")
            return "Possible raid detected from excessive joins."
        return None

    def inspect_message(self, chat_id: int, user_id: int, text: str, entities: list[Any] | None = None) -> list[str]:
        findings: list[str] = []
        now = time.time()
        key = (chat_id, user_id)
        guardian_enabled = self.store.get_setting(chat_id, "guardian", False)
        window = int(self.store.get_setting(chat_id, "flood_window", 10))
        threshold = int(self.store.get_setting(chat_id, "spam_threshold", 5))
        if guardian_enabled:
            window = max(3, window // 2)
            threshold = max(3, threshold - 2)
        messages = self.messages.setdefault(key, [])
        messages.append((now, text))
        messages[:] = [(stamp, msg) for stamp, msg in messages if now - stamp <= window]

        lowered = text.lower()
        antispam_enabled = self.store.get_setting(chat_id, "antispam", True)
        if self.store.get_setting(chat_id, "antilink", False) and _contains_link(lowered, entities):
            findings.append("link_spam")
        if self.store.get_setting(chat_id, "antiflood", True) and len(messages) >= threshold:
            findings.append("flood")
        if antispam_enabled and len({msg for _, msg in messages[-3:]}) == 1 and len(messages) >= 3:
            findings.append("repeated_messages")
        if antispam_enabled and text.count("@") >= 6:
            findings.append("mention_spam")
        if antispam_enabled and _caps_ratio(text) > 0.75 and sum(1 for char in text if char.isalpha()) >= 12:
            findings.append("caps_spam")
        if self.store.get_setting(chat_id, "antiemoji", False) and _emoji_density(text) > 0.65 and len(text) >= 12:
            findings.append("emoji_spam")

        for finding in findings:
            self.store.log_security_event(chat_id, finding, user_id, text[:200])
        return findings

    def threat_level(self, chat_id: int) -> str:
        counts = self.store.security_counts(chat_id, 60)
        score = sum(counts.values())
        if counts.get("raid", 0) or score >= 20:
            return "CRITICAL"
        if score >= 10:
            return "HIGH"
        if score >= 4:
            return "MEDIUM"
        return "LOW"

    def alt_risk(self, chat_id: int, user_id: int, username: str = "") -> tuple[str, list[str]]:
        counts = self.store.security_counts(chat_id, 24 * 60)
        reasons: list[str] = []
        score = 0
        if counts.get("flood", 0) or counts.get("repeated_messages", 0):
            score += 2
            reasons.append("recent spam-like behavior in the group")
        if counts.get("raid", 0):
            score += 2
            reasons.append("joined or appeared during suspicious join timing")
        if username and sum(ch.isdigit() for ch in username) >= 4:
            score += 1
            reasons.append("username contains many digits")
        with self.store.connect() as conn:
            punishments = conn.execute(
                "SELECT COUNT(*) AS count FROM mod_logs WHERE chat_id = ? AND target_id = ?",
                (chat_id, user_id),
            ).fetchone()["count"]
        if punishments:
            score += 2
            reasons.append("previous moderation history exists")
        if score >= 4:
            return "HIGH RISK", reasons
        if score >= 2:
            return "MEDIUM RISK", reasons
        return "LOW RISK", reasons or ["no strong suspicious indicators found"]


def _emoji_density(text: str) -> float:
    if not text:
        return 0.0
    emoji_like = sum(1 for char in text if ord(char) > 10000)
    return emoji_like / max(len(text), 1)


def _caps_ratio(text: str) -> float:
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for char in letters if char.isupper()) / len(letters)


def _contains_link(lowered_text: str, entities: list[Any] | None = None) -> bool:
    needles = ("http://", "https://", "t.me/", "telegram.me/", "www.")
    if any(needle in lowered_text for needle in needles):
        return True
    for entity in entities or []:
        entity_type = str(getattr(entity, "type", "")).lower()
        if entity_type in {"url", "text_link"}:
            return True
        url = str(getattr(entity, "url", "") or "").lower()
        if any(needle in url for needle in needles):
            return True
    return False


store = GroupStore()
security_service = SecurityService(store)
