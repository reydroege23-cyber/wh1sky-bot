"""Inline Telegram Marine admin control panel."""

from __future__ import annotations

import io
import json
import logging
from datetime import datetime
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from config import OWNER_ID
from services.group_management import store


logger = logging.getLogger(__name__)

TOGGLE_KEYS = {
    "antispam": "Anti-spam",
    "antilink": "Anti-link",
    "antiflood": "Anti-flood",
    "captcha": "Captcha",
    "guardian": "Guardian",
    "ai_enabled": "AI replies",
}

PUNISHMENTS = ["mute", "ban", "kick", "warn"]
LANGUAGES = ["en", "ku", "ar", "tr"]
SLOWMODE_STEPS = [0, 5, 10, 30, 60, 300]
WARNING_LIMIT_STEPS = [1, 2, 3, 5, 10]

SETTING_LABELS = {
    "rules": "Rules",
    "welcome": "Welcome",
    "goodbye": "Goodbye",
    "slowmode": "Slowmode",
    "warnings_limit": "Warnings limit",
    "punishment": "Punishment",
    "log_channel": "Log channel",
    "group_language": "Language",
}


def _chat_id(update: Update) -> int:
    if update.effective_chat:
        return int(update.effective_chat.id)
    query = update.callback_query
    if query and query.message:
        return int(query.message.chat_id)
    raise RuntimeError("chat id unavailable")


def _actor_id(update: Update) -> int:
    if update.effective_user:
        return int(update.effective_user.id)
    raise RuntimeError("user id unavailable")


async def _is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if _actor_id(update) == OWNER_ID:
        return True
    member = await context.bot.get_chat_member(_chat_id(update), _actor_id(update))
    return member.status in {"administrator", "creator"}


async def _require_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if await _is_admin(update, context):
        return True
    if update.callback_query:
        await update.callback_query.answer("Admin permission required.", show_alert=True)
    elif update.message:
        await update.message.reply_text("Admin permission required.")
    return False


async def _require_owner(update: Update) -> bool:
    if _actor_id(update) == OWNER_ID:
        return True
    if update.callback_query:
        await update.callback_query.answer("Owner-only control.", show_alert=True)
    elif update.message:
        await update.message.reply_text("Owner-only command.")
    return False


def _main_keyboard(is_owner: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton("Settings", callback_data="panel:settings"),
            InlineKeyboardButton("Protection", callback_data="panel:protection"),
        ],
        [
            InlineKeyboardButton("Messages", callback_data="panel:messages"),
            InlineKeyboardButton("Logs", callback_data="panel:logs"),
        ],
        [
            InlineKeyboardButton("Commands", callback_data="panel:cmds"),
            InlineKeyboardButton("Reload", callback_data="panel:reload"),
        ],
    ]
    if is_owner:
        rows.append([InlineKeyboardButton("Owner Panel", callback_data="panel:owner")])
    return InlineKeyboardMarkup(rows)


def _back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="panel:home")]])


def _protection_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    rows = []
    for key, label in TOGGLE_KEYS.items():
        state = "ON" if store.get_setting(chat_id, key) else "OFF"
        rows.append([InlineKeyboardButton(f"{label}: {state}", callback_data=f"panel:toggle:{key}")])
    rows.append([InlineKeyboardButton("Back", callback_data="panel:home")])
    return InlineKeyboardMarkup(rows)


def _settings_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    settings = store.all_settings(chat_id)
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(f"Slowmode: {settings.get('slowmode', 0)}s", callback_data="panel:cycle:slowmode"),
                InlineKeyboardButton(f"Warns: {settings.get('warnings_limit', 3)}", callback_data="panel:cycle:warnings_limit"),
            ],
            [
                InlineKeyboardButton(f"Punishment: {settings.get('punishment', 'mute')}", callback_data="panel:cycle:punishment"),
                InlineKeyboardButton(f"Language: {settings.get('group_language', 'en')}", callback_data="panel:cycle:group_language"),
            ],
            [
                InlineKeyboardButton("Log Channel", callback_data="panel:log_channel"),
                InlineKeyboardButton("Back", callback_data="panel:home"),
            ],
        ]
    )


def _settings_text(chat_id: int) -> str:
    settings = store.all_settings(chat_id)
    lines = ["Group settings:"]
    for key, label in SETTING_LABELS.items():
        value = settings.get(key, "")
        if isinstance(value, str) and len(value) > 80:
            value = value[:77] + "..."
        lines.append(f"{label}: {value}")
    for key, label in TOGGLE_KEYS.items():
        lines.append(f"{label}: {'ON' if settings.get(key) else 'OFF'}")
    return "\n".join(lines)


async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    is_owner = _actor_id(update) == OWNER_ID
    await update.message.reply_text(
        "Marine admin control panel\nUse buttons below to manage this group.",
        reply_markup=_main_keyboard(is_owner),
    )


async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    await update.message.reply_text(_settings_text(_chat_id(update)), reply_markup=_settings_keyboard(_chat_id(update)))


async def setrules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    value = " ".join(context.args).strip()
    if not value:
        await update.message.reply_text("Usage: /setrules <rules text>")
        return
    store.set_setting(_chat_id(update), "rules", value)
    store.log_action(_chat_id(update), _actor_id(update), "set_rules", reason=value[:200])
    await update.message.reply_text("Rules updated.")


async def setwelcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    value = " ".join(context.args).strip()
    if not value:
        await update.message.reply_text("Usage: /setwelcome <welcome message>")
        return
    store.set_setting(_chat_id(update), "welcome", value)
    store.log_action(_chat_id(update), _actor_id(update), "set_welcome", reason=value[:200])
    await update.message.reply_text("Welcome message updated.")


async def setgoodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    value = " ".join(context.args).strip()
    if not value:
        await update.message.reply_text("Usage: /setgoodbye <goodbye message>")
        return
    store.set_setting(_chat_id(update), "goodbye", value)
    store.log_action(_chat_id(update), _actor_id(update), "set_goodbye", reason=value[:200])
    await update.message.reply_text("Goodbye message updated.")


async def toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    if not context.args:
        await update.message.reply_text(
            "Usage:\n"
            "/toggle <antispam|antilink|antiflood|captcha|guardian|ai_enabled> [on|off]\n"
            "/toggle slowmode <seconds>\n"
            "/toggle warnings_limit <number>\n"
            "/toggle punishment <mute|ban|kick|warn>\n"
            "/toggle log_channel <chat_id|off>\n"
            "/toggle group_language <en|ku|ar|tr>"
        )
        return
    key = context.args[0]
    if key in TOGGLE_KEYS:
        current = bool(store.get_setting(_chat_id(update), key))
        value = not current if len(context.args) == 1 else context.args[1].lower() in {"on", "true", "yes", "1", "enable"}
    elif key == "slowmode" and len(context.args) > 1 and context.args[1].isdigit():
        value = max(0, int(context.args[1]))
        try:
            await context.bot.set_chat_slow_mode_delay(_chat_id(update), value)
        except Exception as e:
            logger.warning("Could not apply Telegram slowmode immediately: %s", e)
    elif key == "warnings_limit" and len(context.args) > 1 and context.args[1].isdigit():
        value = max(1, int(context.args[1]))
    elif key == "punishment" and len(context.args) > 1 and context.args[1] in PUNISHMENTS:
        value = context.args[1]
    elif key == "log_channel" and len(context.args) > 1:
        value = "" if context.args[1].lower() in {"off", "none", "disable"} else context.args[1]
    elif key == "group_language" and len(context.args) > 1 and context.args[1] in LANGUAGES:
        value = context.args[1]
    else:
        await update.message.reply_text("Invalid setting or value. Use /toggle with no arguments for help.")
        return
    store.set_setting(_chat_id(update), key, value)
    store.log_action(_chat_id(update), _actor_id(update), "toggle", reason=f"{key}={value}")
    label = TOGGLE_KEYS.get(key, SETTING_LABELS.get(key, key))
    await update.message.reply_text(f"{label} set to {value}.")


async def cmds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from bot_commands import GROUP_COMMANDS, PRIVATE_COMMANDS

    private = ", ".join(f"/{cmd.command}" for cmd in PRIVATE_COMMANDS)
    groups = ", ".join(f"/{cmd.command}" for cmd in GROUP_COMMANDS)
    await update.message.reply_text(f"Private commands:\n{private}\n\nGroup commands:\n{groups}")


async def reload_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    store.init_schema()
    store.log_action(_chat_id(update), _actor_id(update), "reload_settings")
    await update.message.reply_text("Settings reloaded from SQLite.")


async def logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    rows = store.recent_logs(_chat_id(update), 10)
    text = "\n".join(f"#{row['id']} {row['action']} target={row['target_id']} {row['created_at']}" for row in rows)
    await update.message.reply_text(text or "No logs yet.")


async def resetsettings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    chat_id = _chat_id(update)
    store.reset_settings(chat_id)
    store.log_action(chat_id, _actor_id(update), "reset_settings")
    await update.message.reply_text("Settings reset for this chat only.")


async def exportsettings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    chat_id = _chat_id(update)
    payload = {
        "chat_id": chat_id,
        "exported_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "settings": store.export_settings(chat_id),
    }
    data = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
    store.log_action(chat_id, _actor_id(update), "export_settings")
    await update.message.reply_document(
        io.BytesIO(data),
        filename=f"settings-{chat_id}.json",
        caption="Settings export for this chat.",
    )


async def importsettings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    chat_id = _chat_id(update)
    raw = " ".join(context.args).strip()
    if update.message.reply_to_message and update.message.reply_to_message.document:
        document = update.message.reply_to_message.document
        telegram_file = await document.get_file()
        raw = (await telegram_file.download_as_bytearray()).decode("utf-8")
    if not raw:
        await update.message.reply_text("Usage: /importsettings <json> or reply to a JSON settings export.")
        return
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        await update.message.reply_text(f"Invalid JSON: {exc}")
        return
    settings = payload.get("settings", payload) if isinstance(payload, dict) else {}
    if not isinstance(settings, dict):
        await update.message.reply_text("Invalid settings export.")
        return
    store.import_settings(chat_id, settings)
    store.log_action(chat_id, _actor_id(update), "import_settings")
    await update.message.reply_text("Settings imported for this chat only.")


async def copysettings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_owner(update):
        return
    if len(context.args) < 2 or not all(arg.lstrip("-").isdigit() for arg in context.args[:2]):
        await update.message.reply_text("Usage: /copysettings <source_chat_id> <target_chat_id>")
        return
    source_chat_id = int(context.args[0])
    target_chat_id = int(context.args[1])
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Confirm Copy",
                    callback_data=f"panel:copysettings:{source_chat_id}:{target_chat_id}",
                )
            ],
            [InlineKeyboardButton("Cancel", callback_data="panel:home")],
        ]
    )
    await update.message.reply_text(
        f"Copy settings from {source_chat_id} to {target_chat_id}?\n"
        "This overwrites only the target chat settings.",
        reply_markup=keyboard,
    )


async def panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    if not await _require_admin(update, context):
        return
    await query.answer()
    chat_id = _chat_id(update)
    actor_id = _actor_id(update)
    data = query.data or ""
    parts = data.split(":")
    action = parts[1] if len(parts) > 1 else "home"

    if action == "home":
        await query.edit_message_text("Marine admin control panel", reply_markup=_main_keyboard(actor_id == OWNER_ID))
    elif action == "settings":
        await query.edit_message_text(_settings_text(chat_id), reply_markup=_settings_keyboard(chat_id))
    elif action == "protection":
        await query.edit_message_text("Protection toggles", reply_markup=_protection_keyboard(chat_id))
    elif action == "messages":
        text = (
            f"Rules:\n{store.get_setting(chat_id, 'rules')}\n\n"
            f"Welcome:\n{store.get_setting(chat_id, 'welcome')}\n\n"
            f"Goodbye:\n{store.get_setting(chat_id, 'goodbye')}"
        )
        await query.edit_message_text(text, reply_markup=_back_keyboard())
    elif action == "logs":
        rows = store.recent_logs(chat_id, 10)
        text = "\n".join(f"#{row['id']} {row['action']} target={row['target_id']}" for row in rows) or "No logs yet."
        await query.edit_message_text(text, reply_markup=_back_keyboard())
    elif action == "cmds":
        from bot_commands import GROUP_COMMANDS

        text = "\n".join(f"/{cmd.command} - {cmd.description}" for cmd in GROUP_COMMANDS)
        await query.edit_message_text(text, reply_markup=_back_keyboard())
    elif action == "reload":
        store.init_schema()
        store.log_action(chat_id, actor_id, "panel_reload")
        await query.edit_message_text("Settings reloaded from SQLite.", reply_markup=_back_keyboard())
    elif action == "toggle" and len(parts) == 3 and parts[2] in TOGGLE_KEYS:
        key = parts[2]
        value = not bool(store.get_setting(chat_id, key))
        store.set_setting(chat_id, key, value)
        store.log_action(chat_id, actor_id, "panel_toggle", reason=f"{key}={value}")
        await query.edit_message_text("Protection toggles", reply_markup=_protection_keyboard(chat_id))
    elif action == "cycle" and len(parts) == 3:
        key = parts[2]
        if key == "slowmode":
            value = _next_value(SLOWMODE_STEPS, int(store.get_setting(chat_id, key, 0)))
            try:
                await context.bot.set_chat_slow_mode_delay(chat_id, value)
            except Exception as e:
                logger.warning("Could not apply Telegram slowmode immediately: %s", e)
        elif key == "warnings_limit":
            value = _next_value(WARNING_LIMIT_STEPS, int(store.get_setting(chat_id, key, 3)))
        elif key == "punishment":
            value = _next_value(PUNISHMENTS, str(store.get_setting(chat_id, key, "mute")))
        elif key == "group_language":
            value = _next_value(LANGUAGES, str(store.get_setting(chat_id, key, "en")))
        else:
            await query.edit_message_text("Unknown setting.", reply_markup=_settings_keyboard(chat_id))
            return
        store.set_setting(chat_id, key, value)
        store.log_action(chat_id, actor_id, "panel_setting", reason=f"{key}={value}")
        await query.edit_message_text(_settings_text(chat_id), reply_markup=_settings_keyboard(chat_id))
    elif action == "log_channel":
        await query.edit_message_text(
            "Set log channel with:\n/toggle log_channel <chat_id>\n\nDisable with:\n/toggle log_channel off",
            reply_markup=_settings_keyboard(chat_id),
        )
    elif action == "owner":
        if not await _require_owner(update):
            return
        text = (
            "Owner panel\n"
            f"Status: online\n"
            f"Maintenance: {store.get_setting(chat_id, 'maintenance', False)}\n"
            f"Time: {datetime.utcnow().isoformat()}Z"
        )
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Maintenance", callback_data="panel:owner_maintenance")],
                [InlineKeyboardButton("Backup DB", callback_data="panel:owner_backup")],
                [InlineKeyboardButton("Error Logs", callback_data="panel:owner_errors")],
                [InlineKeyboardButton("Back", callback_data="panel:home")],
            ]
        )
        await query.edit_message_text(text, reply_markup=keyboard)
    elif action == "owner_maintenance":
        if not await _require_owner(update):
            return
        value = not bool(store.get_setting(chat_id, "maintenance", False))
        store.set_setting(chat_id, "maintenance", value)
        store.log_action(chat_id, actor_id, "owner_maintenance", reason=str(value))
        await query.edit_message_text(f"Maintenance mode set to {value}.", reply_markup=_back_keyboard())
    elif action == "owner_backup":
        if not await _require_owner(update):
            return
        path = store.backup()
        await query.message.reply_document(path.open("rb"), filename=path.name)
    elif action == "owner_errors":
        if not await _require_owner(update):
            return
        await query.edit_message_text("Use /logs for recent moderation logs. Runtime errors are in bot.log.", reply_markup=_back_keyboard())
    elif action == "copysettings" and len(parts) == 4:
        if not await _require_owner(update):
            return
        source_chat_id = int(parts[2])
        target_chat_id = int(parts[3])
        store.copy_settings(source_chat_id, target_chat_id)
        store.log_action(target_chat_id, actor_id, "copy_settings", reason=f"from {source_chat_id}")
        await query.edit_message_text(
            f"Copied settings from {source_chat_id} to {target_chat_id}.",
            reply_markup=_back_keyboard(),
        )
    else:
        await query.edit_message_text("Unknown panel action.", reply_markup=_back_keyboard())


COMMANDS: dict[str, Any] = {
    "panel": panel,
    "settings": settings_menu,
    "setrules": setrules,
    "setwelcome": setwelcome,
    "setgoodbye": setgoodbye,
    "toggle": toggle,
    "cmds": cmds,
    "reload": reload_settings,
    "logs": logs,
    "copysettings": copysettings,
    "resetsettings": resetsettings,
    "exportsettings": exportsettings,
    "importsettings": importsettings,
}


def _next_value(options: list[Any], current: Any) -> Any:
    try:
        index = options.index(current)
    except ValueError:
        return options[0]
    return options[(index + 1) % len(options)]
