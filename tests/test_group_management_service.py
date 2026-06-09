from pathlib import Path

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
