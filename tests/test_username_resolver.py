from types import SimpleNamespace

import pytest

from services.group_management import GroupStore


class FakeMessage:
    def __init__(self, text="/ban @known"):
        self.text = text
        self.replies = []

    async def reply_text(self, text, **kwargs):
        self.replies.append(text)


class FakeBot:
    def __init__(self):
        self.banned = []

    async def get_chat_member(self, chat_id, user_id):
        return SimpleNamespace(status="administrator")

    async def get_chat_administrators(self, chat_id):
        return []

    async def get_chat(self, username):
        raise RuntimeError("Telegram cannot globally resolve arbitrary usernames")

    async def ban_chat_member(self, chat_id, user_id):
        self.banned.append((chat_id, user_id))


def update_for(text: str):
    return SimpleNamespace(
        message=FakeMessage(text),
        callback_query=None,
        effective_chat=SimpleNamespace(id=-1001, type="supergroup"),
        effective_user=SimpleNamespace(id=10, username="admin", full_name="Admin"),
    )


def user(user_id=42, username="known"):
    return SimpleNamespace(
        id=user_id,
        username=username,
        first_name="Known",
        last_name="User",
        full_name="Known User",
        is_bot=False,
    )


@pytest.mark.asyncio
async def test_main_ban_resolves_known_username(tmp_path, monkeypatch):
    import main

    test_store = GroupStore(tmp_path / "resolver.db")
    test_store.record_user(-1001, user())
    monkeypatch.setattr(main, "group_store", test_store)

    bot = FakeBot()
    update = update_for("/ban @known")
    context = SimpleNamespace(args=["@known"], bot=bot)

    await main.ban(update, context)

    assert bot.banned == [(-1001, 42)]
    assert any("banned" in reply for reply in update.message.replies)


@pytest.mark.asyncio
async def test_main_ban_unknown_username_guides_admin(tmp_path, monkeypatch):
    import main

    test_store = GroupStore(tmp_path / "resolver.db")
    monkeypatch.setattr(main, "group_store", test_store)

    bot = FakeBot()
    update = update_for("/ban @missing")
    context = SimpleNamespace(args=["@missing"], bot=bot)

    await main.ban(update, context)

    assert bot.banned == []
    assert update.message.replies == [
        "I don't know this user yet. Reply to their message or use their Telegram ID."
    ]


@pytest.mark.asyncio
async def test_group_management_resolver_known_username(tmp_path, monkeypatch):
    from commands import group_management

    test_store = GroupStore(tmp_path / "resolver.db")
    test_store.record_user(-1001, user())
    monkeypatch.setattr(group_management, "store", test_store)

    update = update_for("/tempban @known 5")
    context = SimpleNamespace(args=["@known", "5"], bot=FakeBot())

    target = await group_management.resolve_target(update, context)

    assert target.user_id == 42
    assert target.display_name == "Known User"
