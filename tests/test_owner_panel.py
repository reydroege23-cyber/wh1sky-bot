from types import SimpleNamespace

import pytest

from services.group_management import GroupStore


OWNER_ID = 8577797097


class FakeMessage:
    def __init__(self, text="/ownerpanel"):
        self.text = text
        self.replies = []
        self.documents = []

    async def reply_text(self, text, **kwargs):
        self.replies.append((text, kwargs))

    async def reply_document(self, document, **kwargs):
        self.documents.append((document, kwargs))


class FakeCallbackMessage:
    def __init__(self, chat_id=OWNER_ID):
        self.chat_id = chat_id
        self.edits = []
        self.documents = []

    async def reply_document(self, document, **kwargs):
        self.documents.append((document, kwargs))


class FakeCallback:
    def __init__(self, data):
        self.data = data
        self.answers = []
        self.message = FakeCallbackMessage()
        self.edits = []

    async def answer(self, text=None, show_alert=False):
        self.answers.append((text, show_alert))

    async def edit_message_text(self, text, **kwargs):
        self.edits.append((text, kwargs))


def command_update(user_id=OWNER_ID, chat_type="private", text="/ownerpanel"):
    return SimpleNamespace(
        message=FakeMessage(text),
        callback_query=None,
        effective_user=SimpleNamespace(id=user_id, username="owner", full_name="Owner"),
        effective_chat=SimpleNamespace(id=user_id, type=chat_type, title=None, username=None),
    )


def callback_update(data, user_id=OWNER_ID):
    return SimpleNamespace(
        message=None,
        callback_query=FakeCallback(data),
        effective_user=SimpleNamespace(id=user_id, username="owner", full_name="Owner"),
        effective_chat=SimpleNamespace(id=user_id, type="private", title=None, username=None),
    )


@pytest.mark.asyncio
async def test_ownerpanel_silent_for_non_owner(tmp_path, monkeypatch):
    from commands import owner_panel

    test_store = GroupStore(tmp_path / "owner.db")
    monkeypatch.setattr(owner_panel, "store", test_store)

    update = command_update(user_id=1234)
    await owner_panel.ownerpanel(update, SimpleNamespace(user_data={}))

    assert update.message.replies == []
    assert test_store.recent_logs(1234, 1)[0]["action"] == "unauthorized_owner_panel"


@pytest.mark.asyncio
async def test_ownerpanel_opens_for_owner_private_chat(tmp_path, monkeypatch):
    from commands import owner_panel

    test_store = GroupStore(tmp_path / "owner.db")
    monkeypatch.setattr(owner_panel, "store", test_store)

    update = command_update()
    await owner_panel.ownerpanel(update, SimpleNamespace(user_data={}))

    assert update.message.replies
    assert update.message.replies[0][0] == "Main Owner Panel"


@pytest.mark.asyncio
async def test_owner_group_toggle_is_per_chat(tmp_path, monkeypatch):
    from commands import owner_panel

    test_store = GroupStore(tmp_path / "owner.db")
    monkeypatch.setattr(owner_panel, "store", test_store)
    test_store.set_setting(-1001, "antilink", False)
    test_store.set_setting(-1002, "antilink", False)

    update = callback_update("owner:grouptoggle:-1001:antilink")
    await owner_panel.owner_callback(update, SimpleNamespace(user_data={}))

    assert test_store.get_setting(-1001, "antilink") is True
    assert test_store.get_setting(-1002, "antilink") is False
    assert update.callback_query.edits


@pytest.mark.asyncio
async def test_owner_text_input_saves_personality(tmp_path, monkeypatch):
    from commands import owner_panel

    test_store = GroupStore(tmp_path / "owner.db")
    monkeypatch.setattr(owner_panel, "store", test_store)
    context = SimpleNamespace(user_data={"owner_panel_state": {"kind": "global", "key": "marine_personality"}})
    update = command_update(text="Warm but concise.")

    await owner_panel.owner_text_input(update, context)

    assert test_store.get_bot_setting("marine_personality") == "Warm but concise."
    assert "owner_panel_state" not in context.user_data
    assert update.message.replies[0][0] == "Saved marine_personality."


def test_chat_registry_and_global_settings(tmp_path):
    store = GroupStore(tmp_path / "owner.db")
    chat = SimpleNamespace(id=-1001, type="supergroup", title="My Group", username=None)

    store.register_chat(chat)
    store.set_bot_setting("bot_branding", "Marine Prime", OWNER_ID)

    rows = store.registered_chats()
    assert rows[0]["chat_id"] == -1001
    assert rows[0]["title"] == "My Group"
    assert store.get_bot_setting("bot_branding") == "Marine Prime"
