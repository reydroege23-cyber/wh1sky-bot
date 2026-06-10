from types import SimpleNamespace

import pytest

from config import OWNER_ID
from services.group_management import GroupStore


class FakeMessage:
    def __init__(self, text="https://example.com"):
        self.deleted = False
        self.text = text
        self.message_id = 1
        self.replies = []
        self.sticker = None
        self.entities = []

    async def delete(self):
        self.deleted = True

    async def reply_text(self, text, **kwargs):
        self.replies.append(text)


class FakeBot:
    id = 999

    def __init__(self, status="member", can_delete_messages=True, can_restrict_members=True):
        self.status = status
        self.can_delete_messages = can_delete_messages
        self.can_restrict_members = can_restrict_members
        self.restricted = []
        self.banned = []
        self.unbanned = []
        self.sent_messages = []

    async def get_chat_member(self, chat_id, user_id):
        if user_id == self.id:
            return SimpleNamespace(
                status="administrator",
                can_delete_messages=self.can_delete_messages,
                can_restrict_members=self.can_restrict_members,
            )
        return SimpleNamespace(status=self.status)

    async def restrict_chat_member(self, chat_id, user_id, permissions, until_date=None):
        self.restricted.append((chat_id, user_id, until_date))

    async def ban_chat_member(self, chat_id, user_id):
        self.banned.append((chat_id, user_id))

    async def unban_chat_member(self, chat_id, user_id):
        self.unbanned.append((chat_id, user_id))

    async def send_message(self, chat_id, text, **kwargs):
        self.sent_messages.append((chat_id, text))


def fake_update(chat_id=-1001, user_id=42, chat_type="supergroup", text="https://example.com"):
    return SimpleNamespace(
        message=FakeMessage(text=text),
        effective_chat=SimpleNamespace(id=chat_id, type=chat_type),
        effective_user=SimpleNamespace(id=user_id, is_bot=False),
    )


@pytest.mark.asyncio
async def test_security_defaults_log_only_without_delete_mute_or_ban(tmp_path, monkeypatch):
    import main

    test_store = GroupStore(tmp_path / "security.db")
    monkeypatch.setattr(main, "group_store", test_store)

    update = fake_update()
    bot = FakeBot(status="member")
    context = SimpleNamespace(bot=bot)

    handled = await main._handle_security_findings(update, context, ["link_spam", "mention_spam"])

    assert handled is True
    assert update.message.deleted is False
    assert bot.restricted == []
    assert bot.banned == []
    assert test_store.get_warnings(-1001, 42) == 0
    row = test_store.last_security_event(-1001, 42)
    assert row is not None
    assert row["event_type"] == "security_detection"


@pytest.mark.asyncio
async def test_testmode_prevents_all_actions_even_when_enabled(tmp_path, monkeypatch):
    import main

    test_store = GroupStore(tmp_path / "security.db")
    test_store.set_setting(-1001, "testmode", True)
    test_store.set_setting(-1001, "auto_action_level", "delete")
    test_store.set_setting(-1001, "auto_delete_enabled", True)
    monkeypatch.setattr(main, "group_store", test_store)

    update = fake_update()
    bot = FakeBot(status="member")
    context = SimpleNamespace(bot=bot)

    handled = await main._handle_security_findings(update, context, ["link_spam", "mention_spam"])

    assert handled is True
    assert update.message.deleted is False
    assert bot.restricted == []
    assert bot.banned == []


@pytest.mark.asyncio
async def test_autopunish_off_prevents_mute_and_ban(tmp_path, monkeypatch):
    import main

    test_store = GroupStore(tmp_path / "security.db")
    test_store.set_setting(-1001, "testmode", False)
    test_store.set_setting(-1001, "auto_action_level", "mute")
    test_store.set_setting(-1001, "auto_mute_enabled", True)
    test_store.set_setting(-1001, "autopunish", False)
    monkeypatch.setattr(main, "group_store", test_store)

    update = fake_update(text="@a @b @c @d @e @f https://example.com")
    bot = FakeBot(status="member")
    context = SimpleNamespace(bot=bot)

    handled = await main._handle_security_findings(update, context, ["link_spam", "mention_spam"])

    assert handled is True
    assert bot.restricted == []
    assert bot.banned == []
    assert update.message.deleted is False


@pytest.mark.asyncio
async def test_score_below_90_prevents_mute_and_ban(tmp_path, monkeypatch):
    import main

    test_store = GroupStore(tmp_path / "security.db")
    test_store.set_setting(-1001, "testmode", False)
    test_store.set_setting(-1001, "auto_action_level", "mute")
    test_store.set_setting(-1001, "auto_mute_enabled", True)
    test_store.set_setting(-1001, "autopunish", True)
    monkeypatch.setattr(main, "group_store", test_store)

    update = fake_update()
    bot = FakeBot(status="member")
    context = SimpleNamespace(bot=bot)

    handled = await main._handle_security_findings(update, context, ["link_spam"])

    assert handled is True
    assert bot.restricted == []
    assert bot.banned == []


@pytest.mark.asyncio
async def test_auto_delete_requires_explicit_enable_and_testmode_off(tmp_path, monkeypatch):
    import main

    test_store = GroupStore(tmp_path / "security.db")
    test_store.set_setting(-1001, "testmode", False)
    test_store.set_setting(-1001, "auto_action_level", "delete")
    test_store.set_setting(-1001, "auto_delete_enabled", True)
    monkeypatch.setattr(main, "group_store", test_store)

    update = fake_update()
    bot = FakeBot(status="member")
    context = SimpleNamespace(bot=bot)

    handled = await main._handle_security_findings(update, context, ["link_spam"])

    assert handled is True
    assert update.message.deleted is True
    assert bot.restricted == []
    assert bot.banned == []


@pytest.mark.asyncio
async def test_security_findings_bypass_group_admins(tmp_path, monkeypatch):
    import main

    test_store = GroupStore(tmp_path / "security.db")
    monkeypatch.setattr(main, "group_store", test_store)

    update = fake_update()
    context = SimpleNamespace(bot=FakeBot(status="administrator"))

    handled = await main._handle_security_findings(update, context, ["link_spam"])

    assert handled is False
    assert update.message.deleted is False
    assert test_store.get_warnings(-1001, 42) == 0


@pytest.mark.asyncio
async def test_security_findings_bypass_owner(tmp_path, monkeypatch):
    import main

    test_store = GroupStore(tmp_path / "security.db")
    monkeypatch.setattr(main, "group_store", test_store)

    update = fake_update(user_id=OWNER_ID)
    context = SimpleNamespace(bot=FakeBot(status="member"))

    handled = await main._handle_security_findings(update, context, ["link_spam"])

    assert handled is False
    assert update.message.deleted is False


@pytest.mark.asyncio
async def test_action_without_reason_is_blocked(tmp_path, monkeypatch):
    import main

    test_store = GroupStore(tmp_path / "security.db")
    monkeypatch.setattr(main, "group_store", test_store)

    update = fake_update()
    bot = FakeBot(status="member")
    context = SimpleNamespace(bot=bot)

    handled = await main._handle_security_findings(update, context, [""])

    assert handled is False
    assert update.message.deleted is False
    assert bot.restricted == []
    assert bot.banned == []


@pytest.mark.asyncio
async def test_anti_link_off_ignores_links(tmp_path):
    from services.group_management import SecurityService

    test_store = GroupStore(tmp_path / "security.db")
    security = SecurityService(test_store)

    assert "link_spam" not in security.inspect_message(-1001, 42, "https://example.com")


@pytest.mark.asyncio
async def test_normal_message_and_sticker_do_not_punish(tmp_path, monkeypatch):
    import main

    test_store = GroupStore(tmp_path / "security.db")
    monkeypatch.setattr(main, "group_store", test_store)

    update = fake_update(text="hello everyone")
    bot = FakeBot(status="member")
    context = SimpleNamespace(bot=bot)

    handled = await main._handle_security_findings(update, context, [])

    assert handled is False
    assert update.message.deleted is False
    assert bot.restricted == []
    assert bot.banned == []

    sticker_update = fake_update(text="")
    sticker_update.message.text = None
    sticker_update.message.sticker = SimpleNamespace(file_id="sticker")
    assert await main._handle_security_findings(sticker_update, context, []) is False


@pytest.mark.asyncio
async def test_error_handler_is_silent_and_does_not_dm_owner(tmp_path, monkeypatch):
    import main

    test_store = GroupStore(tmp_path / "security.db")
    monkeypatch.setattr(main, "group_store", test_store)

    update = fake_update()
    bot = FakeBot(status="member")
    context = SimpleNamespace(bot=bot, error=RuntimeError("boom"))

    await main.error_handler(update, context)

    assert update.message.replies == []
    assert bot.sent_messages == []
    actions = [row["action"] for row in test_store.recent_logs(-1001, 10)]
    assert "handler_error" in actions
