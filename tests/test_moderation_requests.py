from types import SimpleNamespace

import pytest

from services.group_management import GroupStore


OWNER_ID = 8577797097


class FakeMessage:
    def __init__(self, text="/ban @target"):
        self.text = text
        self.replies = []
        self.reply_to_message = None
        self.entities = []

    async def reply_text(self, text, **kwargs):
        self.replies.append((text, kwargs))


class FakeCallback:
    def __init__(self, data, chat_id=-1001, user_id=99):
        self.data = data
        self.answers = []
        self.edits = []
        self.message = SimpleNamespace(chat_id=chat_id)

    async def answer(self, text=None, show_alert=False):
        self.answers.append((text, show_alert))

    async def edit_message_text(self, text, **kwargs):
        self.edits.append((text, kwargs))


class FakeBot:
    def __init__(self, actor_status="member"):
        self.actor_status = actor_status
        self.sent = []
        self.banned = []
        self.unbanned = []
        self.restricted = []

    async def get_chat_member(self, chat_id, user_id):
        return SimpleNamespace(status=self.actor_status)

    async def send_message(self, chat_id, text, **kwargs):
        self.sent.append((chat_id, text, kwargs))

    async def ban_chat_member(self, chat_id, user_id, **kwargs):
        self.banned.append((chat_id, user_id, kwargs))

    async def unban_chat_member(self, chat_id, user_id, **kwargs):
        self.unbanned.append((chat_id, user_id, kwargs))

    async def restrict_chat_member(self, chat_id, user_id, permissions, **kwargs):
        self.restricted.append((chat_id, user_id, permissions, kwargs))


class PermissionBot(FakeBot):
    id = 999

    async def get_chat_member(self, chat_id, user_id):
        if user_id == self.id:
            return SimpleNamespace(status="administrator", can_restrict_members=False)
        return SimpleNamespace(status="administrator")


def user(user_id=42, username="target"):
    return SimpleNamespace(
        id=user_id,
        username=username,
        first_name="Target",
        last_name="User",
        full_name="Target User",
        is_bot=False,
    )


def command_update(text="/ban @target", user_id=1234, username="requester", chat_id=-1001):
    return SimpleNamespace(
        message=FakeMessage(text),
        callback_query=None,
        effective_chat=SimpleNamespace(id=chat_id, type="supergroup"),
        effective_user=SimpleNamespace(id=user_id, username=username, full_name="Requester"),
    )


def callback_update(request_id, user_id=99):
    return SimpleNamespace(
        message=None,
        callback_query=FakeCallback(f"modreq:approve:{request_id}"),
        effective_chat=SimpleNamespace(id=-1001, type="supergroup"),
        effective_user=SimpleNamespace(id=user_id, username="admin", full_name="Admin"),
    )


@pytest.mark.asyncio
async def test_direct_moderation_command_no_longer_creates_request(tmp_path, monkeypatch):
    import main

    test_store = GroupStore(tmp_path / "requests.db")
    test_store.set_setting(-1001, "requestsystem", True)
    test_store.record_user(-1001, user())
    monkeypatch.setattr(main, "group_store", test_store)

    update = command_update("/ban @target")
    context = SimpleNamespace(args=["@target"], bot=FakeBot(actor_status="member"))

    await main.ban(update, context)

    assert update.message.replies == []
    assert test_store.moderation_requests(-1001) == []
    assert test_store.recent_logs(-1001, 1)[0]["action"] == "unauthorized_command"


@pytest.mark.asyncio
async def test_admin_ban_requires_marine_restrict_permission(tmp_path, monkeypatch):
    import main

    test_store = GroupStore(tmp_path / "requests.db")
    test_store.record_user(-1001, user())
    monkeypatch.setattr(main, "group_store", test_store)

    update = command_update("/ban @target", user_id=99, username="admin")
    context = SimpleNamespace(args=["@target"], bot=PermissionBot(actor_status="administrator"))

    await main.ban(update, context)

    assert context.bot.banned == []
    assert "can_restrict_members" in update.message.replies[0][0]


@pytest.mark.asyncio
async def test_request_callback_rejects_normal_user_silently(tmp_path, monkeypatch):
    from commands import moderation_requests

    test_store = GroupStore(tmp_path / "requests.db")
    request_id = test_store.create_moderation_request(-1001, 1234, 42, "@target", "BAN", "spam")
    monkeypatch.setattr(moderation_requests, "store", test_store)

    bot = FakeBot(actor_status="member")
    update = callback_update(request_id, user_id=1234)
    context = SimpleNamespace(args=[], bot=bot)

    await moderation_requests.moderation_request_callback(update, context)

    assert bot.banned == []
    assert test_store.moderation_request(request_id)["status"] == "pending"
    assert update.callback_query.answers == [(None, False)]


@pytest.mark.asyncio
async def test_normal_user_creates_moderation_request(tmp_path, monkeypatch):
    from commands import moderation_requests

    test_store = GroupStore(tmp_path / "requests.db")
    test_store.set_setting(-1001, "requestsystem", True)
    test_store.record_user(-1001, user())
    monkeypatch.setattr(moderation_requests, "store", test_store)

    update = command_update("/ban @target")
    context = SimpleNamespace(args=["@target"], bot=FakeBot(actor_status="member"))

    handled = await moderation_requests.maybe_create_request(update, context, "ban")

    assert handled is True
    assert update.message.replies[0][0] == "Request submitted successfully."
    assert context.bot.sent
    row = test_store.moderation_requests(-1001, "pending", 1)[0]
    assert row["action"] == "BAN"
    assert row["target_id"] == 42


@pytest.mark.asyncio
async def test_admin_bypasses_request_system(tmp_path, monkeypatch):
    from commands import moderation_requests

    test_store = GroupStore(tmp_path / "requests.db")
    test_store.set_setting(-1001, "requestsystem", True)
    monkeypatch.setattr(moderation_requests, "store", test_store)

    update = command_update("/ban 42", user_id=99)
    context = SimpleNamespace(args=["42"], bot=FakeBot(actor_status="administrator"))

    handled = await moderation_requests.maybe_create_request(update, context, "ban")

    assert handled is False
    assert test_store.moderation_requests(-1001) == []


@pytest.mark.asyncio
async def test_approve_button_executes_request(tmp_path, monkeypatch):
    from commands import moderation_requests

    test_store = GroupStore(tmp_path / "requests.db")
    request_id = test_store.create_moderation_request(-1001, 1234, 42, "@target", "BAN", "spam")
    monkeypatch.setattr(moderation_requests, "store", test_store)

    bot = FakeBot(actor_status="administrator")
    update = callback_update(request_id)
    context = SimpleNamespace(args=[], bot=bot)

    await moderation_requests.moderation_request_callback(update, context)

    assert bot.banned[0][0:2] == (-1001, 42)
    assert test_store.moderation_request(request_id)["status"] == "approved"
    assert update.callback_query.edits[0][0] == f"Request #{request_id} approved."


@pytest.mark.asyncio
async def test_reject_command_marks_request_rejected(tmp_path, monkeypatch):
    from commands import moderation_requests

    test_store = GroupStore(tmp_path / "requests.db")
    request_id = test_store.create_moderation_request(-1001, 1234, 42, "@target", "MUTE", "loud")
    monkeypatch.setattr(moderation_requests, "store", test_store)

    update = command_update(f"/reject {request_id}", user_id=99, username="admin")
    context = SimpleNamespace(args=[str(request_id), "not", "needed"], bot=FakeBot(actor_status="administrator"))

    await moderation_requests.reject(update, context)

    row = test_store.moderation_request(request_id)
    assert row["status"] == "rejected"
    assert row["resolution_reason"] == "not needed"


@pytest.mark.asyncio
async def test_request_cooldown_limit(tmp_path, monkeypatch):
    from commands import moderation_requests

    test_store = GroupStore(tmp_path / "requests.db")
    test_store.set_setting(-1001, "requestsystem", True)
    test_store.record_user(-1001, user())
    for _ in range(3):
        test_store.create_moderation_request(-1001, 1234, 42, "@target", "BAN", "spam")
    monkeypatch.setattr(moderation_requests, "store", test_store)

    update = command_update("/ban @target")
    context = SimpleNamespace(args=["@target"], bot=FakeBot(actor_status="member"))

    handled = await moderation_requests.maybe_create_request(update, context, "ban")

    assert handled is True
    assert update.message.replies[0][0] == "Request limit reached. Please wait before sending another request."


@pytest.mark.asyncio
async def test_requestsystem_setting_is_per_group(tmp_path, monkeypatch):
    from commands import moderation_requests

    test_store = GroupStore(tmp_path / "requests.db")
    test_store.set_setting(-1001, "requestsystem", True)
    test_store.set_setting(-1002, "requestsystem", False)
    test_store.record_user(-1001, user())
    monkeypatch.setattr(moderation_requests, "store", test_store)

    update_a = command_update("/ban @target", chat_id=-1001)
    update_b = command_update("/ban @target", chat_id=-1002)

    assert await moderation_requests.maybe_create_request(update_a, SimpleNamespace(args=["@target"], bot=FakeBot()), "ban") is True
    assert await moderation_requests.maybe_create_request(update_b, SimpleNamespace(args=["@target"], bot=FakeBot()), "ban") is False
