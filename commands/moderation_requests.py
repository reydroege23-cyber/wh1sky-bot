"""Moderation request workflow for non-admin users."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from telegram import ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from config import OWNER_ID
from services.group_management import TargetUser, store


logger = logging.getLogger(__name__)

REQUEST_ACTIONS = {
    "ban": "BAN",
    "unban": "UNBAN",
    "kick": "KICK",
    "mute": "MUTE",
    "unmute": "UNMUTE",
    "tempban": "TEMPBAN",
    "tempmute": "TEMPMUTE",
    "warn": "WARN",
    "clearwarns": "CLEARWARNS",
    "clear_warns": "CLEARWARNS",
    "enough": "ENOUGH",
    "unenough": "UNENOUGH",
}


def _chat_id(update: Update) -> int:
    return int(update.effective_chat.id)


def _actor_id(update: Update) -> int:
    return int(update.effective_user.id)


def _display_user(user: Any) -> str:
    username = getattr(user, "username", None)
    if username:
        return f"@{username}"
    return getattr(user, "full_name", None) or getattr(user, "first_name", None) or str(getattr(user, "id", "unknown"))


async def is_admin_or_owner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if _actor_id(update) == OWNER_ID:
        return True
    try:
        member = await context.bot.get_chat_member(_chat_id(update), _actor_id(update))
        return member.status in {"administrator", "creator"}
    except Exception:
        return False


async def resolve_request_target(update: Update, context: ContextTypes.DEFAULT_TYPE) -> TargetUser | None:
    msg = update.message
    reply = getattr(msg, "reply_to_message", None)
    if reply and getattr(reply, "from_user", None):
        user = reply.from_user
        store.record_user(_chat_id(update), user)
        return TargetUser(int(user.id), _display_user(user), getattr(user, "username", None))
    for entity in list(getattr(msg, "entities", None) or []):
        mentioned_user = getattr(entity, "user", None)
        if mentioned_user:
            store.record_user(_chat_id(update), mentioned_user)
            return TargetUser(int(mentioned_user.id), _display_user(mentioned_user), getattr(mentioned_user, "username", None))
    if context.args:
        raw = context.args[0].strip()
        if raw.lstrip("-").isdigit():
            return TargetUser(int(raw), raw)
        if raw.startswith("@"):
            return store.resolve_known_user(_chat_id(update), raw) or TargetUser(None, raw)  # type: ignore[arg-type]
    return None


def _reason_and_duration(action: str, context: ContextTypes.DEFAULT_TYPE) -> tuple[str, str | None]:
    args = list(context.args or [])
    duration = None
    reason_start = 1
    if action in {"TEMPBAN", "TEMPMUTE"} and len(args) > 1:
        duration = args[1]
        reason_start = 2
    reason = " ".join(args[reason_start:]).strip() or "No reason provided."
    return reason, duration


def _request_keyboard(request_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("Approve", callback_data=f"modreq:approve:{request_id}"),
            InlineKeyboardButton("Reject", callback_data=f"modreq:reject:{request_id}"),
        ]]
    )


async def maybe_create_request(update: Update, context: ContextTypes.DEFAULT_TYPE, command_name: str) -> bool:
    action = REQUEST_ACTIONS.get(command_name.lower())
    if not action or not update.message or not update.effective_chat or not update.effective_user:
        return False
    if await is_admin_or_owner(update, context):
        return False
    chat_id = _chat_id(update)
    if not store.get_setting(chat_id, "requestsystem", False):
        return False
    requester_id = _actor_id(update)
    if store.moderation_request_count(chat_id, requester_id, 10) >= 3:
        await update.message.reply_text("Request limit reached. Please wait before sending another request.")
        return True
    target = await resolve_request_target(update, context)
    if not target:
        await update.message.reply_text("I don't know this user yet. Reply to their message or use their Telegram ID.")
        return True
    reason, duration = _reason_and_duration(action, context)
    request_id = store.create_moderation_request(
        chat_id,
        requester_id,
        target.user_id,
        target.display_name,
        action,
        reason,
        duration,
    )
    requester = _display_user(update.effective_user)
    text = (
        f"{action.title()} Request\n\n"
        f"Target: {target.display_name}\n"
        f"Requested by: {requester}\n"
        f"Reason: {reason}"
    )
    if duration:
        text += f"\nDuration: {duration}"
    await update.message.reply_text("Request submitted successfully.")
    await context.bot.send_message(chat_id, text, reply_markup=_request_keyboard(request_id))
    return True


async def moderation_request_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.data:
        return
    parts = query.data.split(":")
    if len(parts) != 3:
        return
    decision, request_id_raw = parts[1], parts[2]
    if not request_id_raw.isdigit():
        return
    if not await is_admin_or_owner(update, context):
        await query.answer(None, show_alert=False)
        return
    request_id = int(request_id_raw)
    row = store.moderation_request(request_id)
    if not row:
        await query.answer("Request not found.", show_alert=True)
        return
    if row["status"] != "pending":
        await query.answer(f"Already {row['status']}.", show_alert=True)
        return
    if decision == "approve":
        try:
            if not await _bot_can_execute_request(context, row):
                await query.answer("Marine lacks the required permission.", show_alert=True)
                return
            await execute_request_action(context, row, _actor_id(update))
        except Exception as exc:
            logger.exception("Failed to approve moderation request %s: %s", request_id, exc)
            await query.answer("Action failed. Check Marine permissions.", show_alert=True)
            return
        store.resolve_moderation_request(request_id, "approved", _actor_id(update), "Approved by inline button")
        await query.edit_message_text(f"Request #{request_id} approved.")
    else:
        store.resolve_moderation_request(request_id, "rejected", _actor_id(update), "Rejected by inline button")
        await query.edit_message_text(f"Request #{request_id} rejected.")
    await query.answer()


async def execute_request_action(context: ContextTypes.DEFAULT_TYPE, row: Any, admin_id: int = OWNER_ID) -> None:
    chat_id = int(row["chat_id"])
    target_id = int(row["target_id"]) if row["target_id"] is not None else None
    action = str(row["action"]).upper()
    reason = row["reason"] or "No reason provided."
    duration = row["duration"]
    if target_id is None:
        raise ValueError("request has no target_id")

    if action in {"BAN", "ENOUGH"}:
        if action == "ENOUGH":
            store.add_permanent_ban(chat_id, target_id, reason, admin_id)
        await context.bot.ban_chat_member(chat_id, target_id)
    elif action in {"UNBAN", "UNENOUGH"}:
        if action == "UNENOUGH":
            store.remove_permanent_ban(chat_id, target_id, admin_id)
        await context.bot.unban_chat_member(chat_id, target_id)
    elif action == "KICK":
        await context.bot.ban_chat_member(chat_id, target_id)
        await context.bot.unban_chat_member(chat_id, target_id)
    elif action in {"MUTE", "TEMPMUTE"}:
        until = None
        if action == "TEMPMUTE":
            minutes = int(duration) if duration and str(duration).isdigit() else 30
            until = datetime.utcnow() + timedelta(minutes=minutes)
        await context.bot.restrict_chat_member(chat_id, target_id, ChatPermissions(can_send_messages=False), until_date=until)
    elif action == "UNMUTE":
        await context.bot.restrict_chat_member(chat_id, target_id, ChatPermissions(can_send_messages=True))
    elif action == "TEMPBAN":
        minutes = int(duration) if duration and str(duration).isdigit() else 60
        await context.bot.ban_chat_member(chat_id, target_id, until_date=datetime.utcnow() + timedelta(minutes=minutes))
    elif action == "WARN":
        store.add_warning(chat_id, target_id)
    elif action == "CLEARWARNS":
        store.clear_warnings(chat_id, target_id)
    else:
        raise ValueError(f"unsupported action {action}")
    store.log_action(chat_id, admin_id, f"request_execute_{action.lower()}", target_id, reason)


async def _bot_can_execute_request(context: ContextTypes.DEFAULT_TYPE, row: Any) -> bool:
    bot_id = getattr(context.bot, "id", None)
    if bot_id is None:
        return True
    action = str(row["action"]).upper()
    if action in {"BAN", "UNBAN", "KICK", "MUTE", "UNMUTE", "TEMPBAN", "TEMPMUTE", "ENOUGH", "UNENOUGH"}:
        permission = "can_restrict_members"
    else:
        return True
    try:
        member = await context.bot.get_chat_member(int(row["chat_id"]), bot_id)
    except Exception:
        return True
    return bool(getattr(member, permission, False))


async def requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin_or_owner(update, context):
        return
    rows = store.moderation_requests(_chat_id(update), "pending", 10)
    text = "\n".join(f"#{row['id']} {row['action']} target={row['target_display']} by={row['requester_id']}" for row in rows)
    await update.message.reply_text(text or "No pending moderation requests.")


async def requestinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin_or_owner(update, context):
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /requestinfo <id>")
        return
    row = store.moderation_request(int(context.args[0]))
    if not row or int(row["chat_id"]) != _chat_id(update):
        await update.message.reply_text("Request not found.")
        return
    await update.message.reply_text(
        f"Request #{row['id']}\n"
        f"Action: {row['action']}\n"
        f"Status: {row['status']}\n"
        f"Target: {row['target_display']} ({row['target_id']})\n"
        f"Requester: {row['requester_id']}\n"
        f"Reason: {row['reason']}\n"
        f"Resolution: {row['resolution_reason'] or ''}"
    )


async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _resolve_from_command(update, context, "approved")


async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _resolve_from_command(update, context, "rejected")


async def _resolve_from_command(update: Update, context: ContextTypes.DEFAULT_TYPE, status: str):
    if not await is_admin_or_owner(update, context):
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(f"Usage: /{'approve' if status == 'approved' else 'reject'} <id> [reason]")
        return
    request_id = int(context.args[0])
    row = store.moderation_request(request_id)
    if not row or int(row["chat_id"]) != _chat_id(update):
        await update.message.reply_text("Request not found.")
        return
    if row["status"] != "pending":
        await update.message.reply_text(f"Request already {row['status']}.")
        return
    reason = " ".join(context.args[1:]).strip() or f"{status.title()} by command"
    if status == "approved":
        if not await _bot_can_execute_request(context, row):
            await update.message.reply_text("Marine lacks the required permission.")
            return
        await execute_request_action(context, row, _actor_id(update))
    store.resolve_moderation_request(request_id, status, _actor_id(update), reason)
    await update.message.reply_text(f"Request #{request_id} {status}.")


async def cancelrequest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.effective_chat:
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /cancelrequest <id>")
        return
    request_id = int(context.args[0])
    row = store.moderation_request(request_id)
    if not row or int(row["chat_id"]) != _chat_id(update):
        await update.message.reply_text("Request not found.")
        return
    if row["status"] != "pending":
        await update.message.reply_text(f"Request already {row['status']}.")
        return
    if int(row["requester_id"]) != _actor_id(update) and not await is_admin_or_owner(update, context):
        return
    store.resolve_moderation_request(request_id, "cancelled", _actor_id(update), "Cancelled by requester/admin")
    await update.message.reply_text(f"Request #{request_id} cancelled.")


async def requestsystem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin_or_owner(update, context):
        return
    if not context.args:
        await update.message.reply_text(f"requestsystem: {store.get_setting(_chat_id(update), 'requestsystem', False)}")
        return
    value = context.args[0].lower() in {"on", "true", "1", "yes", "enable"}
    store.set_setting(_chat_id(update), "requestsystem", value)
    store.log_action(_chat_id(update), _actor_id(update), "set_requestsystem", reason=str(value))
    await update.message.reply_text(f"requestsystem set to {value}.")


COMMANDS: dict[str, Any] = {
    "requests": requests,
    "requestinfo": requestinfo,
    "approve": approve,
    "reject": reject,
    "cancelrequest": cancelrequest,
    "requestsystem": requestsystem,
}
