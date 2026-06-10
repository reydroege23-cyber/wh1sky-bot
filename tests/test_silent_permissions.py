from types import SimpleNamespace

import pytest

from services.group_management import GroupStore


class FakeMessage:
    def __init__(self, text="/ban @target"):
        self.text = text
        self.replies = []

    async def reply_text(self, text, **kwargs):
        self.replies.append(text)


class FakeCallbackQuery:
    def __init__(self, data="panel:owner", chat_id=-1001):
        self.data = data
        self.answers = []
        self.message = SimpleNamespace(chat_id=chat_id)

    async def answer(self, text=None, show_alert=False):
        self.answers.append((text, show_alert))


class FakeBot:
    async def get_chat_member(self, chat_id, user_id):
        return SimpleNamespace(status="member")


def command_update(text="/ban @target", chat_id=-1001, user_id=1234):
    return SimpleNamespace(
        message=FakeMessage(text),
        callback_query=None,
        effective_chat=SimpleNamespace(id=chat_id, type="supergroup"),
        effective_user=SimpleNamespace(id=user_id, username="tester", full_name="Tester"),
    )


def callback_update(data="panel:owner", chat_id=-1001, user_id=1234):
    return SimpleNamespace(
        message=None,
        callback_query=FakeCallbackQuery(data, chat_id),
        effective_chat=None,
        effective_user=SimpleNamespace(id=user_id, username="tester", full_name="Tester"),
    )


@pytest.mark.asyncio
async def test_main_admin_only_fails_silently_and_logs(tmp_path, monkeypatch):
    import main

    test_store = GroupStore(tmp_path / "main-permissions.db")
    monkeypatch.setattr(main, "group_store", test_store)

    called = False

    @main.admin_only
    async def protected(update, context):
        nonlocal called
        called = True
        await update.message.reply_text("ran")

    update = command_update("/ban @target")
    await protected(update, SimpleNamespace(bot=FakeBot()))

    assert called is False
    assert update.message.replies == []
    row = test_store.recent_logs(-1001, 1)[0]
    assert row["action"] == "unauthorized_command"
    assert "command=/ban" in row["reason"]


@pytest.mark.asyncio
async def test_main_owner_only_respects_visible_mode(tmp_path, monkeypatch):
    import main

    test_store = GroupStore(tmp_path / "main-visible.db")
    test_store.set_setting(-1001, "silent_permission_mode", False)
    monkeypatch.setattr(main, "group_store", test_store)

    @main.owner_only
    async def protected(update, context):
        await update.message.reply_text("ran")

    update = command_update("/backupdb")
    await protected(update, SimpleNamespace(bot=FakeBot()))

    assert update.message.replies == ["You don't have permission to use this command."]
    assert test_store.recent_logs(-1001, 1)[0]["action"] == "unauthorized_command"


@pytest.mark.asyncio
async def test_group_management_admin_requirement_fails_silently(tmp_path, monkeypatch):
    from commands import group_management

    test_store = GroupStore(tmp_path / "group-management.db")
    monkeypatch.setattr(group_management, "store", test_store)

    update = command_update("/guardian on")
    allowed = await group_management._require_admin(update, SimpleNamespace(bot=FakeBot()))

    assert allowed is False
    assert update.message.replies == []
    row = test_store.recent_logs(-1001, 1)[0]
    assert row["action"] == "unauthorized_command"
    assert "command=/guardian" in row["reason"]


@pytest.mark.asyncio
async def test_admin_panel_callback_requirement_fails_silently(tmp_path, monkeypatch):
    from commands import admin_panel

    test_store = GroupStore(tmp_path / "admin-panel.db")
    monkeypatch.setattr(admin_panel, "store", test_store)

    update = callback_update("panel:owner")
    allowed = await admin_panel._require_admin(update, SimpleNamespace(bot=FakeBot()))

    assert allowed is False
    assert update.callback_query.answers == [(None, False)]
    row = test_store.recent_logs(-1001, 1)[0]
    assert row["action"] == "unauthorized_command"
    assert "command=panel:owner" in row["reason"]


@pytest.mark.asyncio
async def test_economy_owner_commands_fail_silently(tmp_path, monkeypatch):
    import admin_economy

    test_store = GroupStore(tmp_path / "economy-permissions.db")
    monkeypatch.setattr(admin_economy, "store", test_store)

    update = command_update("/addcoins 42 10")
    denied = await admin_economy._deny_if_not_owner(update)

    assert denied is True
    assert update.message.replies == []
    row = test_store.recent_logs(-1001, 1)[0]
    assert row["action"] == "unauthorized_command"
    assert "command=/addcoins" in row["reason"]
