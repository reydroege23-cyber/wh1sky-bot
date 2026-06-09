from bot_commands import GROUP_COMMANDS, PRIVATE_COMMANDS, command_names


def test_command_menu_entries_are_valid_for_telegram():
    commands = [*PRIVATE_COMMANDS, *GROUP_COMMANDS]
    assert commands
    for command in commands:
        assert command.command == command.command.lower()
        assert "_" not in command.command
        assert 1 <= len(command.command) <= 32
        assert command.description
        assert len(command.description) <= 256


def test_required_commands_are_exposed():
    names = command_names()
    for required in {
        "start",
        "help",
        "ban",
        "unban",
        "mute",
        "unmute",
        "warn",
        "warns",
        "clearwarns",
        "enough",
        "checkalt",
        "guardian",
        "report",
        "rules",
        "setrules",
        "setwelcome",
        "setgoodbye",
        "settings",
        "security",
        "testsecurity",
        "aireplies",
        "aimode",
        "aicooldown",
        "stats",
        "ping",
        "marine",
    }:
        assert required in names
