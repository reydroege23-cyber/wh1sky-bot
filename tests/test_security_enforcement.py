from types import SimpleNamespace

import pytest

from services.group_management import GroupStore


class FakeMessage:
    def __init__(self):
        self.deleted = False
        self.text = "https://example.com"
        self.message_id = 1

    async def delete(self):
        self.deleted = True


class FakeBot:
    def __init__(self, status="member"):
        self.status = status
        self.restricted = []
        self.banned = []
        self.unbanned = []

    async def get_chat_member(self, chat_id, user_id):
        return SimpleNamespace(status=self.status)

    async def restrict_chat_member(self, chat_id, user_id, permissions, until_date=None):
        self.restricted.append((chat_id, user_id, until_date))

    async def ban_chat_member(self, chat_id, user_id):
        self.banned.append((chat_id, user_id))

    async def unban_chat_member(self, chat_id, user_id):
        self.unbanned.append((chat_id, user_id))


def fake_update(chat_id=-1001, user_id=42, chat_type="supergroup"):
    return SimpleNamespace(
        message=FakeMessage(),
        effective_chat=SimpleNamespace(id=chat_id, type=chat_type),
        effective_user=SimpleNamespace(id=user_id),
    )


@pytest.mark.asyncio
async def test_security_findings_delete_and_punish_when_limit_reached(tmp_path, monkeypatch):
    import main

    test_store = GroupStore(tmp_path / "security.db")
    test_store.set_setting(-1001, "warnings_limit", 1)
    test_store.set_setting(-1001, "punishment", "mute")
    monkeypatch.setattr(main, "group_store", test_store)

    update = fake_update()
    bot = FakeBot(status="member")
    context = SimpleNamespace(bot=bot)

    handled = await main._handle_security_findings(update, context, ["link_spam"])

    assert handled is True
    assert update.message.deleted is True
    assert bot.restricted
    assert test_store.get_warnings(-1001, 42) == 0


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
