"""Private owner control panel for Marine."""

from __future__ import annotations

import io
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from config import OWNER_ID
from services.group_management import store


logger = logging.getLogger(__name__)

OWNER_STATE_KEY = "owner_panel_state"

GROUP_TOGGLES = {
    "ai_enabled": "AI",
    "antispam": "Anti-spam",
    "antilink": "Anti-link",
    "guardian": "Guardian",
    "silent_permission_mode": "Silent perms",
}

GROUP_TEXT_SETTINGS = {
    "rules": "Rules",
    "welcome": "Welcome",
    "goodbye": "Goodbye",
    "warning_limit": "Warning limit",
    "punishment": "Punishment",
    "log_channel": "Log channel",
}

GLOBAL_TEXT_SETTINGS = {
    "bot_branding": "Bot branding",
    "owner_lore": "Owner lore/glazing replies",
}


def _actor_id(update: Update) -> int | None:
    return int(update.effective_user.id) if update.effective_user else None


def _chat_id(update: Update) -> int | None:
    return int(update.effective_chat.id) if update.effective_chat else None


def _is_owner(update: Update) -> bool:
    return _actor_id(update) == OWNER_ID


async def _silent_non_owner(update: Update) -> bool:
    if _is_owner(update):
        return False
    logger.warning(
        "Unauthorized owner panel attempt user=%s chat=%s command=%s",
        _actor_id(update),
        _chat_id(update),
        getattr(update.message, "text", "") if update.message else getattr(update.callback_query, "data", ""),
    )
    try:
        store.log_action(_chat_id(update) or 0, _actor_id(update), "unauthorized_owner_panel")
    except Exception:
        pass
    if update.callback_query:
        await update.callback_query.answer(None, show_alert=False)
    return True


def _main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Bot Status", callback_data="owner:status"), InlineKeyboardButton("Groups", callback_data="owner:groups")],
            [InlineKeyboardButton("Global Bot Settings", callback_data="owner:global"), InlineKeyboardButton("AI Personality", callback_data="owner:personality")],
            [InlineKeyboardButton("Broadcast", callback_data="owner:broadcast"), InlineKeyboardButton("Logs & Errors", callback_data="owner:errors")],
            [InlineKeyboardButton("Database Backup", callback_data="owner:backup"), InlineKeyboardButton("Maintenance Mode", callback_data="owner:maintenance")],
        ]
    )


def _back_keyboard(target: str = "owner:home") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data=target)]])


def _groups_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for row in store.registered_chats(False, 20):
        title = str(row["title"] or row["chat_id"])[:32]
        rows.append([InlineKeyboardButton(title, callback_data=f"owner:group:{row['chat_id']}")])
    rows.append([InlineKeyboardButton("Back", callback_data="owner:home")])
    return InlineKeyboardMarkup(rows)


def _group_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("Protection Settings", callback_data=f"owner:groupsec:{chat_id}")],
        [InlineKeyboardButton("Welcome & Rules", callback_data=f"owner:grouptext:{chat_id}")],
        [InlineKeyboardButton("AI Settings", callback_data=f"owner:grouptoggle:{chat_id}:ai_enabled")],
        [InlineKeyboardButton("Command Manager", callback_data=f"owner:edit:{chat_id}:command_permissions")],
        [InlineKeyboardButton("Back to Groups", callback_data="owner:groups")],
    ]
    return InlineKeyboardMarkup(rows)


def _group_security_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    rows = []
    for key, label in GROUP_TOGGLES.items():
        state = "ON" if store.get_setting(chat_id, key) else "OFF"
        rows.append([InlineKeyboardButton(f"{label}: {state}", callback_data=f"owner:grouptoggle:{chat_id}:{key}")])
    rows.append([InlineKeyboardButton("Warning Limit", callback_data=f"owner:edit:{chat_id}:warning_limit")])
    rows.append([InlineKeyboardButton("Punishment", callback_data=f"owner:edit:{chat_id}:punishment")])
    rows.append([InlineKeyboardButton("Log Channel", callback_data=f"owner:edit:{chat_id}:log_channel")])
    rows.append([InlineKeyboardButton("Back", callback_data=f"owner:group:{chat_id}")])
    return InlineKeyboardMarkup(rows)


def _group_text_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Edit Rules", callback_data=f"owner:edit:{chat_id}:rules")],
            [InlineKeyboardButton("Edit Welcome", callback_data=f"owner:edit:{chat_id}:welcome")],
            [InlineKeyboardButton("Edit Goodbye", callback_data=f"owner:edit:{chat_id}:goodbye")],
            [InlineKeyboardButton("Back", callback_data=f"owner:group:{chat_id}")],
        ]
    )


def _global_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Bot Name/Branding", callback_data="owner:globaledit:bot_branding")],
            [InlineKeyboardButton("Owner Lore", callback_data="owner:globaledit:owner_lore")],
            [InlineKeyboardButton("Back", callback_data="owner:home")],
        ]
    )


def _personality_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Edit Marine Personality", callback_data="owner:globaledit:marine_personality")],
            [InlineKeyboardButton("Back", callback_data="owner:home")],
        ]
    )


def _status_text() -> str:
    chats = store.registered_chats(False, 100)
    settings = store.all_bot_settings()
    return (
        "Marine owner status\n"
        f"Time: {datetime.utcnow().isoformat(timespec='seconds')}Z\n"
        f"Tracked groups: {len(chats)}\n"
        f"Maintenance: {settings.get('maintenance_mode', False)}\n"
        f"Branding: {settings.get('bot_branding', 'Marine')}"
    )


async def ownerpanel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _silent_non_owner(update):
        return
    if update.effective_chat and update.effective_chat.type != "private":
        await update.message.reply_text("Open Marine in private chat to use the owner panel.")
        return
    store.register_chat(update.effective_chat)
    store.log_admin_action(_chat_id(update) or 0, OWNER_ID, "owner_panel_open")
    await update.message.reply_text("Main Owner Panel", reply_markup=_main_keyboard())


async def groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _silent_non_owner(update):
        return
    await update.message.reply_text("Groups where Marine has been seen:", reply_markup=_groups_keyboard())


async def editgroup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _silent_non_owner(update):
        return
    if not context.args or not context.args[0].lstrip("-").isdigit():
        await update.message.reply_text("Usage: /editgroup <chat_id>")
        return
    chat_id = int(context.args[0])
    await update.message.reply_text(f"Editing group {chat_id}", reply_markup=_group_keyboard(chat_id))


async def globalsettings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _silent_non_owner(update):
        return
    settings = store.all_bot_settings()
    lines = [f"{key}: {value}" for key, value in settings.items()] or ["No global settings yet."]
    await update.message.reply_text("\n".join(lines), reply_markup=_global_keyboard())


async def editpersonality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _silent_non_owner(update):
        return
    current = store.get_bot_setting("marine_personality", "Default Marine personality is active.")
    await update.message.reply_text(str(current)[:3500], reply_markup=_personality_keyboard())


async def setmarinepersonality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _silent_non_owner(update):
        return
    text = " ".join(context.args).strip()
    if not text:
        context.user_data[OWNER_STATE_KEY] = {"kind": "global", "key": "marine_personality"}
        await update.message.reply_text("Send the new Marine personality text. /cancel to abort.")
        return
    _set_global("marine_personality", text)
    await update.message.reply_text("Marine personality updated.")


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _silent_non_owner(update):
        return
    text = " ".join(context.args).strip()
    if not text:
        context.user_data[OWNER_STATE_KEY] = {"kind": "broadcast"}
        await update.message.reply_text("Send the broadcast message. I will ask for confirmation before sending.")
        return
    context.user_data[OWNER_STATE_KEY] = {"kind": "confirm_broadcast", "text": text}
    await update.message.reply_text(f"Confirm broadcast to tracked groups?\n\n{text}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Confirm", callback_data="owner:confirm_broadcast"), InlineKeyboardButton("Cancel", callback_data="owner:cancel")]]))


async def backupdb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _silent_non_owner(update):
        return
    path = store.backup()
    store.log_admin_action(_chat_id(update) or 0, OWNER_ID, "owner_backupdb", detail=str(path))
    await update.message.reply_document(path.open("rb"), filename=path.name)


def _redact(text: str) -> str:
    text = re.sub(r"\b\d{8,10}:[A-Za-z0-9_-]{25,}\b", "[REDACTED_TELEGRAM_TOKEN]", text)
    text = re.sub(r"sk-[A-Za-z0-9_-]{20,}", "[REDACTED_API_KEY]", text)
    return text


async def errors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _silent_non_owner(update):
        return
    log_path = Path("bot.log")
    text = _redact(log_path.read_text(encoding="utf-8", errors="ignore")[-3500:] if log_path.exists() else "No log file.")
    await update.message.reply_text(text)


async def maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _silent_non_owner(update):
        return
    if not context.args:
        value = not bool(store.get_bot_setting("maintenance_mode", False))
    else:
        value = context.args[0].lower() in {"on", "true", "1", "yes", "enable"}
    _set_global("maintenance_mode", value)
    await update.message.reply_text(f"Maintenance mode set to {value}.")


async def owner_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    if await _silent_non_owner(update):
        return
    data = query.data or ""
    parts = data.split(":")
    action = parts[1] if len(parts) > 1 else "home"
    await query.answer()

    if action == "home":
        await query.edit_message_text("Main Owner Panel", reply_markup=_main_keyboard())
    elif action == "status":
        await query.edit_message_text(_status_text(), reply_markup=_back_keyboard())
    elif action == "groups":
        await query.edit_message_text("Select a group:", reply_markup=_groups_keyboard())
    elif action == "group" and len(parts) == 3:
        chat_id = int(parts[2])
        settings = store.all_settings(chat_id)
        await query.edit_message_text(
            f"Editing group {chat_id}\nAnti-link: {settings.get('antilink')}\nGuardian: {settings.get('guardian')}",
            reply_markup=_group_keyboard(chat_id),
        )
    elif action == "groupsec" and len(parts) == 3:
        await query.edit_message_text("Protection Settings", reply_markup=_group_security_keyboard(int(parts[2])))
    elif action == "grouptext" and len(parts) == 3:
        await query.edit_message_text("Welcome & Rules", reply_markup=_group_text_keyboard(int(parts[2])))
    elif action == "grouptoggle" and len(parts) == 4:
        chat_id = int(parts[2])
        key = parts[3]
        current = bool(store.get_setting(chat_id, key))
        store.set_setting(chat_id, key, not current)
        store.log_admin_action(chat_id, OWNER_ID, "owner_group_toggle", detail=f"{key}={not current}")
        await query.edit_message_text("Protection Settings", reply_markup=_group_security_keyboard(chat_id))
    elif action == "edit" and len(parts) == 4:
        chat_id = int(parts[2])
        key = parts[3]
        context.user_data[OWNER_STATE_KEY] = {"kind": "group", "chat_id": chat_id, "key": key}
        await query.edit_message_text(f"Send new value for {key} in group {chat_id}. /cancel to abort.")
    elif action == "global":
        await query.edit_message_text("Global Bot Settings", reply_markup=_global_keyboard())
    elif action == "personality":
        await query.edit_message_text("AI Personality", reply_markup=_personality_keyboard())
    elif action == "globaledit" and len(parts) == 3:
        key = parts[2]
        context.user_data[OWNER_STATE_KEY] = {"kind": "global", "key": key}
        await query.edit_message_text(f"Send new value for {key}. /cancel to abort.")
    elif action == "broadcast":
        context.user_data[OWNER_STATE_KEY] = {"kind": "broadcast"}
        await query.edit_message_text("Send the broadcast message. I will ask for confirmation before sending.")
    elif action == "confirm_broadcast":
        await _send_broadcast(query, context)
    elif action == "errors":
        log_path = Path("bot.log")
        text = _redact(log_path.read_text(encoding="utf-8", errors="ignore")[-3500:] if log_path.exists() else "No log file.")
        await query.edit_message_text(text, reply_markup=_back_keyboard())
    elif action == "backup":
        path = store.backup()
        store.log_admin_action(_chat_id(update) or 0, OWNER_ID, "owner_backupdb", detail=str(path))
        await query.message.reply_document(path.open("rb"), filename=path.name)
    elif action == "maintenance":
        value = not bool(store.get_bot_setting("maintenance_mode", False))
        _set_global("maintenance_mode", value)
        await query.edit_message_text(f"Maintenance mode set to {value}.", reply_markup=_back_keyboard())
    elif action == "cancel":
        context.user_data.pop(OWNER_STATE_KEY, None)
        await query.edit_message_text("Cancelled.", reply_markup=_back_keyboard())


async def owner_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get(OWNER_STATE_KEY):
        return
    if await _silent_non_owner(update):
        return
    text = (update.message.text or "").strip()
    if text == "/cancel":
        context.user_data.pop(OWNER_STATE_KEY, None)
        await update.message.reply_text("Cancelled.")
        return
    state = context.user_data.pop(OWNER_STATE_KEY)
    kind = state.get("kind")
    if kind == "group":
        chat_id = int(state["chat_id"])
        key = state["key"]
        value = _validate_group_value(key, text)
        if value is None:
            await update.message.reply_text("Invalid value. Try again from /ownerpanel.")
            return
        store.set_setting(chat_id, key, value)
        store.log_admin_action(chat_id, OWNER_ID, "owner_group_setting", detail=f"{key}={value}")
        await update.message.reply_text(f"Saved {key} for group {chat_id}.")
    elif kind == "global":
        key = state["key"]
        _set_global(key, text)
        await update.message.reply_text(f"Saved {key}.")
    elif kind == "broadcast":
        context.user_data[OWNER_STATE_KEY] = {"kind": "confirm_broadcast", "text": text}
        await update.message.reply_text(
            f"Confirm broadcast to tracked groups?\n\n{text}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Confirm", callback_data="owner:confirm_broadcast"), InlineKeyboardButton("Cancel", callback_data="owner:cancel")]]),
        )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _silent_non_owner(update):
        return
    context.user_data.pop(OWNER_STATE_KEY, None)
    await update.message.reply_text("Cancelled.")


def _set_global(key: str, value: Any) -> None:
    store.set_bot_setting(key, value, OWNER_ID)
    store.log_admin_action(0, OWNER_ID, "owner_global_setting", detail=f"{key}={str(value)[:200]}")


def _validate_group_value(key: str, raw: str) -> Any:
    if key == "warning_limit":
        return max(1, min(100, int(raw))) if raw.isdigit() else None
    if key == "punishment":
        value = raw.lower()
        return value if value in {"warn", "mute", "kick", "ban"} else None
    if key == "log_channel":
        if raw.lower() in {"off", "none", "disable"}:
            return ""
        return raw if raw.lstrip("-").isdigit() else None
    if key == "command_permissions":
        return raw
    return raw[:4000]


async def _send_broadcast(query: Any, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = context.user_data.pop(OWNER_STATE_KEY, {})
    text = state.get("text")
    if not text:
        await query.edit_message_text("No broadcast text pending.", reply_markup=_back_keyboard())
        return
    sent = 0
    failed = 0
    for row in store.registered_chats(False, 1000):
        try:
            await context.bot.send_message(int(row["chat_id"]), text)
            sent += 1
        except Exception as exc:
            failed += 1
            logger.warning("Broadcast failed for %s: %s", row["chat_id"], exc)
    store.log_admin_action(0, OWNER_ID, "owner_broadcast", detail=f"sent={sent}; failed={failed}")
    await query.edit_message_text(f"Broadcast complete. Sent: {sent}. Failed: {failed}.", reply_markup=_back_keyboard())


COMMANDS: dict[str, Any] = {
    "ownerpanel": ownerpanel,
    "groups": groups,
    "editgroup": editgroup,
    "globalsettings": globalsettings,
    "editpersonality": editpersonality,
    "setmarinepersonality": setmarinepersonality,
    "broadcast": broadcast,
    "backupdb": backupdb,
    "errors": errors,
    "maintenance": maintenance,
    "cancel": cancel,
}
