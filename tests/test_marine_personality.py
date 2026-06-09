from types import SimpleNamespace

from marine_personality import marine_system_prompt


def test_marine_prompt_enforces_identity():
    prompt = marine_system_prompt("group")

    assert "Your name is Marine" in prompt
    assert "female AI assistant" in prompt
    assert "Never say you are ChatGPT" in prompt
    assert "I was developed to help and protect this community." in prompt
    assert "Current chat context: group chat" in prompt


def test_marine_prompt_supports_private_context():
    prompt = marine_system_prompt("private")

    assert "Current chat context: private chat" in prompt
    assert "longer conversation" in prompt


def test_should_marine_reply_only_when_invoked_in_groups():
    import main

    bot = SimpleNamespace(id=99, username="MarineBot")
    group = SimpleNamespace(type="supergroup")

    plain = SimpleNamespace(
        effective_chat=group,
        message=SimpleNamespace(text="hello everyone", reply_to_message=None),
    )
    named = SimpleNamespace(
        effective_chat=group,
        message=SimpleNamespace(text="Marine can you help?", reply_to_message=None),
    )
    mentioned = SimpleNamespace(
        effective_chat=group,
        message=SimpleNamespace(text="@MarineBot help", reply_to_message=None),
    )
    replied = SimpleNamespace(
        effective_chat=group,
        message=SimpleNamespace(
            text="can you explain?",
            reply_to_message=SimpleNamespace(from_user=SimpleNamespace(id=99)),
        ),
    )

    assert main._should_marine_reply(plain, SimpleNamespace(bot=bot)) is False
    assert main._should_marine_reply(named, SimpleNamespace(bot=bot)) is True
    assert main._should_marine_reply(mentioned, SimpleNamespace(bot=bot)) is True
    assert main._should_marine_reply(replied, SimpleNamespace(bot=bot)) is True


def test_should_marine_reply_in_private_chat():
    import main

    update = SimpleNamespace(
        effective_chat=SimpleNamespace(type="private"),
        message=SimpleNamespace(text="hello", reply_to_message=None),
    )

    assert main._should_marine_reply(update, SimpleNamespace(bot=SimpleNamespace())) is True
