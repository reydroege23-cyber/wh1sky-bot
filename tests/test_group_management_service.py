from pathlib import Path
import sqlite3

from services.group_management import GroupStore, SecurityService


def test_settings_logs_and_permanent_bans(tmp_path: Path):
    store = GroupStore(tmp_path / "group.db")
    store.set_setting(1, "guardian", True)
    assert store.get_setting(1, "guardian") is True

    store.log_action(1, 10, "ban", 20, "spam")
    assert store.recent_logs(1, 1)[0]["action"] == "ban"

    store.add_permanent_ban(1, 99, "enough", 10)
    assert store.is_permanently_banned(1, 99)
    store.remove_permanent_ban(1, 99, 10)
    assert not store.is_permanently_banned(1, 99)


def test_security_service_scores_alt_risk(tmp_path: Path):
    store = GroupStore(tmp_path / "group.db")
    security = SecurityService(store)
    store.log_action(1, 10, "warn", 42, "spam")
    store.log_security_event(1, "flood", 42, "burst")

    risk, reasons = security.alt_risk(1, 42, "user12345")
    assert risk in {"MEDIUM RISK", "HIGH RISK"}
    assert reasons


def test_security_service_detects_message_findings(tmp_path: Path):
    store = GroupStore(tmp_path / "group.db")
    store.set_setting(1, "antilink", True)
    security = SecurityService(store)

    findings = security.inspect_message(1, 42, "visit https://example.com @a @b @c @d @e @f")
    assert "link_spam" in findings
    assert "mention_spam" in findings


def test_settings_are_isolated_per_chat(tmp_path: Path):
    store = GroupStore(tmp_path / "group.db")

    store.set_setting(-1001, "guardian", True)
    store.set_setting(-1001, "rules", "Group A rules")
    store.set_setting(-1001, "welcome", "Welcome to A")

    store.set_setting(-1002, "guardian", False)
    store.set_setting(-1002, "rules", "Group B rules")
    store.set_setting(-1002, "welcome", "Welcome to B")

    assert store.get_setting(-1001, "guardian") is True
    assert store.get_setting(-1002, "guardian") is False
    assert store.get_setting(-1001, "rules") == "Group A rules"
    assert store.get_setting(-1002, "rules") == "Group B rules"
    assert store.get_setting(-1001, "welcome") == "Welcome to A"
    assert store.get_setting(-1002, "welcome") == "Welcome to B"


def test_antilink_scanning_is_chat_scoped(tmp_path: Path):
    store = GroupStore(tmp_path / "group.db")
    security = SecurityService(store)

    store.set_setting(-1001, "antilink", True)
    store.set_setting(-1002, "antilink", False)

    assert "link_spam" in security.inspect_message(-1001, 42, "https://example.com")
    assert "link_spam" not in security.inspect_message(-1002, 42, "https://example.com")


def test_antispam_and_antiraid_can_be_disabled_per_chat(tmp_path: Path):
    store = GroupStore(tmp_path / "group.db")
    security = SecurityService(store)

    store.set_setting(-1001, "antispam", False)
    store.set_setting(-1001, "antiraid", False)

    assert security.inspect_message(-1001, 42, "@a @b @c @d @e @f") == []
    security.inspect_message(-1001, 42, "same")
    security.inspect_message(-1001, 42, "same")
    assert "repeated_messages" not in security.inspect_message(-1001, 42, "same")
    assert security.record_join(-1001, 42) is None


def test_warnings_are_isolated_per_chat(tmp_path: Path):
    store = GroupStore(tmp_path / "group.db")

    assert store.add_warning(-1001, 42) == 1
    assert store.add_warning(-1001, 42) == 2
    assert store.add_warning(-1002, 42) == 1
    assert store.get_warnings(-1001, 42) == 2
    assert store.get_warnings(-1002, 42) == 1
    store.clear_warnings(-1001, 42)
    assert store.get_warnings(-1001, 42) == 0
    assert store.get_warnings(-1002, 42) == 1


def test_reset_export_import_and_copy_are_chat_scoped(tmp_path: Path):
    store = GroupStore(tmp_path / "group.db")

    store.set_setting(-1001, "guardian", True)
    store.set_setting(-1001, "rules", "Source rules")
    store.set_setting(-1002, "rules", "Target rules")

    exported = store.export_settings(-1001)
    assert exported["guardian"] is True
    assert exported["rules"] == "Source rules"

    store.import_settings(-1003, exported)
    assert store.get_setting(-1003, "guardian") is True
    assert store.get_setting(-1003, "rules") == "Source rules"

    store.copy_settings(-1001, -1002)
    assert store.get_setting(-1002, "rules") == "Source rules"

    store.reset_settings(-1002)
    assert store.get_setting(-1002, "guardian") is False
    assert store.get_setting(-1002, "rules") == "No rules have been set yet."
    assert store.get_setting(-1001, "rules") == "Source rules"


def test_legacy_key_value_chat_settings_migrate_to_wide_table(tmp_path: Path):
    db_path = tmp_path / "legacy.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE chat_settings (
                chat_id INTEGER NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY(chat_id, key)
            )
            """
        )
        conn.execute(
            "INSERT INTO chat_settings(chat_id, key, value, updated_at) VALUES (?, ?, ?, ?)",
            (-1001, "guardian", "true", "2026-06-09T00:00:00"),
        )
        conn.execute(
            "INSERT INTO chat_settings(chat_id, key, value, updated_at) VALUES (?, ?, ?, ?)",
            (-1001, "rules", '"Legacy rules"', "2026-06-09T00:00:00"),
        )

    store = GroupStore(db_path)

    assert store.get_setting(-1001, "guardian") is True
    assert store.get_setting(-1001, "rules") == "Legacy rules"
    with store.connect() as conn:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(chat_settings)").fetchall()}
    assert "chat_id" in columns
    assert "guardian_enabled" in columns
    assert "key" not in columns
