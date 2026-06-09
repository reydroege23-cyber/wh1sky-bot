from commands.admin_panel import COMMANDS, TOGGLE_KEYS, _next_value, _protection_keyboard, _settings_keyboard
from services.group_management import GroupStore


def test_panel_commands_are_registered():
    for command in {
        "panel",
        "settings",
        "setrules",
        "setwelcome",
        "setgoodbye",
        "toggle",
        "cmds",
        "reload",
        "logs",
        "copysettings",
        "resetsettings",
        "exportsettings",
        "importsettings",
    }:
        assert command in COMMANDS


def test_toggle_keys_have_buttons(tmp_path, monkeypatch):
    from commands import admin_panel

    test_store = GroupStore(tmp_path / "panel.db")
    monkeypatch.setattr(admin_panel, "store", test_store)

    keyboard = _protection_keyboard(123)
    callback_data = [
        button.callback_data
        for row in keyboard.inline_keyboard
        for button in row
        if button.callback_data
    ]
    for key in TOGGLE_KEYS:
        assert f"panel:toggle:{key}" in callback_data


def test_settings_keyboard_controls_scalar_settings(tmp_path, monkeypatch):
    from commands import admin_panel

    test_store = GroupStore(tmp_path / "panel.db")
    monkeypatch.setattr(admin_panel, "store", test_store)

    keyboard = _settings_keyboard(123)
    callback_data = [
        button.callback_data
        for row in keyboard.inline_keyboard
        for button in row
        if button.callback_data
    ]
    for expected in {
        "panel:cycle:slowmode",
        "panel:cycle:warnings_limit",
        "panel:cycle:punishment",
        "panel:cycle:group_language",
        "panel:log_channel",
    }:
        assert expected in callback_data


def test_next_value_cycles():
    assert _next_value([0, 5, 10], 0) == 5
    assert _next_value([0, 5, 10], 10) == 0
    assert _next_value(["mute", "ban"], "missing") == "mute"
