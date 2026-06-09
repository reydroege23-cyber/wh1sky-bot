from types import SimpleNamespace

import pytest

from services.group_management import GroupStore


class FakeSentMessage:
    def __init__(self):
        self.text = None

    async def edit_text(self, text):
        self.text = text


class FakeMessage:
    def __init__(self, text="Marine hello", message_id=1, reply_to_message=None):
        self.text = text
        self.message_id = message_id
        self.reply_to_message = reply_to_message
        self.sent = []

    async def reply_text(self, text, **kwargs):
        sent = FakeSentMessage()
        sent.text = text
        self.sent.append(sent)
        return sent


class FakeBot:
    id = 999
    username = "MarineBot"

    def __init__(self, member=None):
        self.member = member or SimpleNamespace(status="member")

    async def get_chat_member(self, chat_id, user_id):
        return self.member


def fake_update(
    text="Marine hello",
    chat_id=-1001,
    user_id=42,
    message_id=1,
    chat_type="supergroup",
    is_bot=False,
    reply_to_message=None,
):
    return SimpleNamespace(
        message=FakeMessage(text=text, message_id=message_id, reply_to_message=reply_to_message),
        effective_chat=SimpleNamespace(id=chat_id, type=chat_type),
        effective_user=SimpleNamespace(id=user_id, is_bot=is_bot),
    )


@pytest.fixture(autouse=True)
def clear_ai_state(monkeypatch):
    import main

    main.AI_MEMORY.clear()
    main.AI_COOLDOWNS.clear()
    main.AI_RESPONDED_MESSAGES.clear()

    async def noop_save():
        return None

    monkeypatch.setattr(main, "queue_data_save", noop_save)


@pytest.mark.asyncio
async def test_marine_replies_to_direct_reply_in_group(tmp_path, monkeypatch):
    import main

    test_store = GroupStore(tmp_path / "ai.db")
    monkeypatch.setattr(main, "group_store", test_store)

    captured = {}

    async def fake_ask_ai(prompt, chat_context="group", is_owner=False):
        captured["prompt"] = prompt
        captured["chat_context"] = chat_context
        captured["is_owner"] = is_owner
        return "Marine response"

    monkeypatch.setattr(main, "ask_ai", fake_ask_ai)

    reply = SimpleNamespace(text="Previous Marine message", from_user=SimpleNamespace(id=999, is_bot=True))
    update = fake_update(text="Can you explain?", reply_to_message=reply)
    context = SimpleNamespace(bot=FakeBot())

    assert main._marine_trigger_reason(update, context) == "reply"
    handled = await main._send_marine_ai_response(update, context, update.message.text, "reply")

    assert handled is True
    assert captured["chat_context"] == "group"
    assert captured["is_owner"] is False
    assert "Previous Marine message" in captured["prompt"]
    assert update.message.sent[-1].text == "Marine response"


@pytest.mark.asyncio
async def test_marine_does_not_auto_reply_when_disabled(tmp_path, monkeypatch):
    import main

    test_store = GroupStore(tmp_path / "ai.db")
    test_store.set_setting(-1001, "aireplies", False)
    monkeypatch.setattr(main, "group_store", test_store)

    async def fake_ask_ai(*args, **kwargs):
        raise AssertionError("AI should not be called")

    monkeypatch.setattr(main, "ask_ai", fake_ask_ai)

    update = fake_update(text="Marine hello")
    handled = await main._send_marine_ai_response(update, SimpleNamespace(bot=FakeBot()), update.message.text, "name")

    assert handled is False


@pytest.mark.asyncio
async def test_marine_group_cooldown_prevents_spam(tmp_path, monkeypatch):
    import main

    test_store = GroupStore(tmp_path / "ai.db")
    test_store.set_setting(-1001, "ai_cooldown", 10)
    monkeypatch.setattr(main, "group_store", test_store)
    calls = {"count": 0}

    async def fake_ask_ai(*args, **kwargs):
        calls["count"] += 1
        return "ok"

    monkeypatch.setattr(main, "ask_ai", fake_ask_ai)

    context = SimpleNamespace(bot=FakeBot())
    first = fake_update(text="Marine one", message_id=1)
    second = fake_update(text="Marine two", message_id=2)

    assert await main._send_marine_ai_response(first, context, first.message.text, "name") is True
    assert await main._send_marine_ai_response(second, context, second.message.text, "name") is False
    assert calls["count"] == 1


@pytest.mark.asyncio
async def test_marine_ignores_bots_and_restricted_users(tmp_path, monkeypatch):
    import main

    test_store = GroupStore(tmp_path / "ai.db")
    monkeypatch.setattr(main, "group_store", test_store)

    async def fake_ask_ai(*args, **kwargs):
        raise AssertionError("AI should not be called")

    monkeypatch.setattr(main, "ask_ai", fake_ask_ai)

    bot_user_update = fake_update(is_bot=True)
    assert await main._send_marine_ai_response(bot_user_update, SimpleNamespace(bot=FakeBot()), "hi", "name") is False

    restricted = SimpleNamespace(status="restricted", can_send_messages=False)
    restricted_update = fake_update(message_id=2)
    assert await main._send_marine_ai_response(
        restricted_update,
        SimpleNamespace(bot=FakeBot(member=restricted)),
        "hi",
        "name",
    ) is False


@pytest.mark.asyncio
async def test_owner_interaction_passes_owner_context(tmp_path, monkeypatch):
    import main

    test_store = GroupStore(tmp_path / "ai.db")
    monkeypatch.setattr(main, "group_store", test_store)
    captured = {}

    async def fake_ask_ai(prompt, chat_context="group", is_owner=False):
        captured["is_owner"] = is_owner
        return "For Whisky the Great"

    monkeypatch.setattr(main, "ask_ai", fake_ask_ai)

    update = fake_update(user_id=8577797097, text="Marine, who am I?")
    handled = await main._send_marine_ai_response(update, SimpleNamespace(bot=FakeBot()), update.message.text, "name")

    assert handled is True
    assert captured["is_owner"] is True
