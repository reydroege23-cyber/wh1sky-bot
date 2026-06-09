"""Command handlers for advanced group management features."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from telegram import ChatPermissions, Update
from telegram.ext import ContextTypes

from config import OWNER_ID
from services.group_management import TargetUser, security_service, store


ALT_NOTICE = "This is not proof that accounts belong to the same person. Manual review is recommended."


def _chat_id(update: Update) -> int:
    return int(update.effective_chat.id)


def _actor_id(update: Update) -> int:
    return int(update.effective_user.id)


async def _is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    member = await context.bot.get_chat_member(_chat_id(update), _actor_id(update))
    return member.status in {"administrator", "creator"}


async def _require_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if await _is_admin(update, context):
        return True
    await update.message.reply_text("Admin permission required.")
    return False


async def _require_owner(update: Update) -> bool:
    if _actor_id(update) == OWNER_ID:
        return True
    await update.message.reply_text("Owner-only command.")
    return False


async def resolve_target(update: Update, context: ContextTypes.DEFAULT_TYPE) -> TargetUser | None:
    msg = update.message
    if msg and msg.reply_to_message and msg.reply_to_message.from_user:
        user = msg.reply_to_message.from_user
        return TargetUser(user.id, user.full_name or user.username or str(user.id))
    if context.args:
        raw = context.args[0].strip()
        if raw.lstrip("-").isdigit():
            return TargetUser(int(raw), raw)
        if raw.startswith("@"):
            return TargetUser(0, raw)
    return None


def _reason(context: ContextTypes.DEFAULT_TYPE, skip: int = 1) -> str:
    return " ".join(context.args[skip:]).strip() or "No reason provided"


async def tempban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    target = await resolve_target(update, context)
    if not target or target.user_id == 0:
        await update.message.reply_text("Use /tempban by reply or numeric user ID. Example: /tempban 123456 60 spam")
        return
    minutes = int(context.args[1]) if len(context.args) > 1 and context.args[1].isdigit() else 60
    until = datetime.utcnow() + timedelta(minutes=minutes)
    await context.bot.ban_chat_member(_chat_id(update), target.user_id, until_date=until)
    store.log_action(_chat_id(update), _actor_id(update), "tempban", target.user_id, _reason(context, 2))
    await update.message.reply_text(f"Temp-banned {target.display_name} for {minutes} minutes.")


async def tempmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    target = await resolve_target(update, context)
    if not target or target.user_id == 0:
        await update.message.reply_text("Use /tempmute by reply or numeric user ID. Example: /tempmute 123456 30 flood")
        return
    minutes = int(context.args[1]) if len(context.args) > 1 and context.args[1].isdigit() else 30
    perms = ChatPermissions(can_send_messages=False)
    await context.bot.restrict_chat_member(_chat_id(update), target.user_id, perms, until_date=datetime.utcnow() + timedelta(minutes=minutes))
    store.log_action(_chat_id(update), _actor_id(update), "tempmute", target.user_id, _reason(context, 2))
    await update.message.reply_text(f"Muted {target.display_name} for {minutes} minutes.")


async def enough(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_owner(update):
        return
    chat_id = _chat_id(update)
    if context.args and context.args[0].lower() in {"list", "view"}:
        rows = store.permanent_bans(chat_id)
        text = "\n".join(f"{row['user_id']} - {row['reason'] or ''}" for row in rows) or "No permanent bans."
        await update.message.reply_text(text)
        return
    if context.args and context.args[0].lower() in {"remove", "del", "delete"}:
        if len(context.args) < 2 or not context.args[1].lstrip("-").isdigit():
            await update.message.reply_text("Usage: /enough remove <user_id>")
            return
        user_id = int(context.args[1])
        store.remove_permanent_ban(chat_id, user_id, _actor_id(update))
        await update.message.reply_text(f"Removed {user_id} from permanent bans.")
        return
    target = await resolve_target(update, context)
    if not target or target.user_id == 0:
        await update.message.reply_text("Use /enough by reply or numeric user ID. Use /enough list or /enough remove <id>.")
        return
    reason = _reason(context, 1)
    store.add_permanent_ban(chat_id, target.user_id, reason, _actor_id(update))
    await context.bot.ban_chat_member(chat_id, target.user_id)
    await update.message.reply_text(f"Permanent re-ban enabled for {target.display_name}.")


async def modlogs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    rows = store.recent_logs(_chat_id(update), 10)
    if not rows:
        await update.message.reply_text("No moderation logs yet.")
        return
    lines = [f"#{row['id']} {row['action']} target={row['target_id']} by={row['actor_id']} {row['created_at']}" for row in rows]
    await update.message.reply_text("\n".join(lines))


async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    target = await resolve_target(update, context)
    if not target or target.user_id == 0:
        await update.message.reply_text("Use /history by reply or numeric user ID.")
        return
    with store.connect() as conn:
        rows = conn.execute(
            "SELECT * FROM mod_logs WHERE chat_id = ? AND target_id = ? ORDER BY id DESC LIMIT 10",
            (_chat_id(update), target.user_id),
        ).fetchall()
    text = "\n".join(f"#{row['id']} {row['action']} {row['reason'] or ''}" for row in rows) or "No history."
    await update.message.reply_text(text)


async def audit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    settings = store.all_settings(_chat_id(update))
    level = security_service.threat_level(_chat_id(update))
    enabled = [key for key, value in settings.items() if isinstance(value, bool) and value]
    await update.message.reply_text(f"Threat level: {level}\nEnabled protections: {', '.join(enabled) or 'none'}")


async def modstats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    with store.connect() as conn:
        logs = conn.execute("SELECT COUNT(*) AS c FROM mod_logs WHERE chat_id = ?", (_chat_id(update),)).fetchone()["c"]
        reports = conn.execute("SELECT COUNT(*) AS c FROM reports WHERE chat_id = ?", (_chat_id(update),)).fetchone()["c"]
        incidents = conn.execute("SELECT COUNT(*) AS c FROM security_events WHERE chat_id = ?", (_chat_id(update),)).fetchone()["c"]
    await update.message.reply_text(f"Moderation actions: {logs}\nReports: {reports}\nSecurity incidents: {incidents}")


async def purge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to the first message to purge from.")
        return
    start = update.message.reply_to_message.message_id
    end = update.message.message_id
    deleted = 0
    for message_id in range(start, end + 1):
        try:
            await context.bot.delete_message(_chat_id(update), message_id)
            deleted += 1
        except Exception:
            pass
    store.log_action(_chat_id(update), _actor_id(update), "purge", reason=f"{deleted} messages")
    notice = await context.bot.send_message(_chat_id(update), f"Purged {deleted} messages.")
    try:
        await context.bot.delete_message(_chat_id(update), notice.message_id)
    except Exception:
        pass


async def purgeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    target = await resolve_target(update, context)
    if not target:
        await update.message.reply_text("Use /purgeuser by replying to a user's message.")
        return
    store.log_action(_chat_id(update), _actor_id(update), "purgeuser", target.user_id, "requested")
    await update.message.reply_text("Telegram does not expose bulk delete by user directly; use /purge on a message range. Request logged.")


async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await resolve_target(update, context)
    reason = _reason(context, 1 if target else 0)
    store.add_report(_chat_id(update), _actor_id(update), target.user_id if target else None, reason)
    await update.message.reply_text("Report submitted to moderators.")


async def pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message to pin it.")
        return
    await context.bot.pin_chat_message(_chat_id(update), update.message.reply_to_message.message_id)
    store.log_action(_chat_id(update), _actor_id(update), "pin", reason=str(update.message.reply_to_message.message_id))
    await update.message.reply_text("Pinned.")


async def unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    await context.bot.unpin_chat_message(_chat_id(update))
    store.log_action(_chat_id(update), _actor_id(update), "unpin")
    await update.message.reply_text("Unpinned latest pinned message.")


async def slowmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    seconds = int(context.args[0]) if context.args and context.args[0].isdigit() else 0
    await context.bot.set_chat_slow_mode_delay(_chat_id(update), seconds)
    store.set_setting(_chat_id(update), "slowmode", seconds)
    store.log_action(_chat_id(update), _actor_id(update), "slowmode", reason=str(seconds))
    await update.message.reply_text(f"Slowmode set to {seconds} seconds.")


async def tagall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    await update.message.reply_text("Telegram bots cannot enumerate all members. Use pinned announcements or admin-only broadcast flows.")


async def hidetag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await tagall(update, context)


async def toggle_setting(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    if not await _require_admin(update, context):
        return
    if not context.args:
        current = store.get_setting(_chat_id(update), key)
        await update.message.reply_text(f"{key}: {current}")
        return
    value = context.args[0].lower() in {"on", "true", "yes", "enable", "enabled", "1"}
    store.set_setting(_chat_id(update), key, value)
    store.log_action(_chat_id(update), _actor_id(update), f"set_{key}", reason=str(value))
    await update.message.reply_text(f"{key} set to {value}.")


async def guardian(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await toggle_setting(update, context, "guardian")


async def antispam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await toggle_setting(update, context, "antispam")


async def antilink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await toggle_setting(update, context, "antilink")


async def antiflood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await toggle_setting(update, context, "antiflood")


async def antiemoji(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await toggle_setting(update, context, "antiemoji")


async def antiraid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await toggle_setting(update, context, "antiraid")


async def captcha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await toggle_setting(update, context, "captcha")


async def aireplies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await toggle_setting(update, context, "aireplies")


async def aimode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    modes = {"normal", "friendly", "professional", "playful"}
    chat_id = _chat_id(update)
    if not context.args:
        await update.message.reply_text(f"aimode: {store.get_setting(chat_id, 'aimode', 'normal')}")
        return
    mode = context.args[0].lower()
    if mode not in modes:
        await update.message.reply_text("Usage: /aimode <normal|friendly|professional|playful>")
        return
    store.set_setting(chat_id, "aimode", mode)
    store.log_action(chat_id, _actor_id(update), "set_aimode", reason=mode)
    await update.message.reply_text(f"AI mode set to {mode}.")


async def aicooldown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    chat_id = _chat_id(update)
    if not context.args:
        await update.message.reply_text(f"aicooldown: {store.get_setting(chat_id, 'ai_cooldown', 10)} seconds")
        return
    if not context.args[0].isdigit():
        await update.message.reply_text("Usage: /aicooldown <seconds>")
        return
    seconds = max(0, min(3600, int(context.args[0])))
    store.set_setting(chat_id, "ai_cooldown", seconds)
    store.log_action(chat_id, _actor_id(update), "set_ai_cooldown", reason=str(seconds))
    await update.message.reply_text(f"AI reply cooldown set to {seconds} seconds.")


async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    target = await resolve_target(update, context)
    await update.message.reply_text(f"Verified {target.display_name if target else 'user'}.")
    store.log_action(_chat_id(update), _actor_id(update), "verify", target.user_id if target else None)


async def unverify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    target = await resolve_target(update, context)
    await update.message.reply_text(f"Unverified {target.display_name if target else 'user'}.")
    store.log_action(_chat_id(update), _actor_id(update), "unverify", target.user_id if target else None)


async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    counts = store.security_counts(_chat_id(update), 60)
    await update.message.reply_text(f"Threat level: {security_service.threat_level(_chat_id(update))}\nRecent incidents: {counts}")


async def security(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    chat_id = _chat_id(update)
    settings = store.all_settings(chat_id)
    counts = store.security_counts(chat_id, 60)
    lines = [
        f"Threat level: {security_service.threat_level(chat_id)}",
        f"Guardian: {settings.get('guardian')}",
        f"Anti-spam: {settings.get('antispam')}",
        f"Anti-link: {settings.get('antilink')}",
        f"Anti-flood: {settings.get('antiflood')}",
        f"Anti-emoji: {settings.get('antiemoji')}",
        f"Anti-raid: {settings.get('antiraid')}",
        f"Punishment: {settings.get('punishment')}",
        f"Warning limit: {settings.get('warnings_limit')}",
        f"Recent incidents: {counts or 'none'}",
    ]
    await update.message.reply_text("\n".join(lines))


async def testsecurity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    sample = " ".join(context.args).strip() or "https://example.com @a @b @c @d @e @f"
    findings = security_service.inspect_message(_chat_id(update), _actor_id(update), sample)
    await update.message.reply_text(f"Test findings: {findings or 'none'}")


async def threatlevel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await scan(update, context)


async def checkalt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    target = await resolve_target(update, context)
    if not target:
        await update.message.reply_text("Use /checkalt by reply or numeric user ID.")
        return
    risk, reasons = security_service.alt_risk(_chat_id(update), target.user_id, target.display_name)
    await update.message.reply_text(f"{risk}\nIndicators: {', '.join(reasons)}\n\n{ALT_NOTICE}")


async def checkalts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await checkalt(update, context)


async def suspicious(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await checkalt(update, context)


async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(str(store.get_setting(_chat_id(update), "rules")))


async def setrules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    value = " ".join(context.args).strip()
    if not value:
        await update.message.reply_text("Usage: /setrules <rules text>")
        return
    store.set_setting(_chat_id(update), "rules", value)
    await update.message.reply_text("Rules updated.")


async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(str(store.get_setting(_chat_id(update), "welcome")))


async def setwelcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    store.set_setting(_chat_id(update), "welcome", " ".join(context.args).strip())
    await update.message.reply_text("Welcome message updated.")


async def goodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(str(store.get_setting(_chat_id(update), "goodbye")))


async def setgoodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    store.set_setting(_chat_id(update), "goodbye", " ".join(context.args).strip())
    await update.message.reply_text("Goodbye message updated.")


async def notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    names = store.list_notes(_chat_id(update))
    await update.message.reply_text("Notes: " + (", ".join(names) if names else "none"))


async def save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /save <name> <text>")
        return
    store.save_note(_chat_id(update), context.args[0], " ".join(context.args[1:]), _actor_id(update))
    await update.message.reply_text("Note saved.")


async def get(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /get <name>")
        return
    value = store.get_note(_chat_id(update), context.args[0])
    await update.message.reply_text(value or "Note not found.")


async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    if not context.args:
        await update.message.reply_text("Usage: /delete <name>")
        return
    await update.message.reply_text("Deleted." if store.delete_note(_chat_id(update), context.args[0]) else "Note not found.")


async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = store.all_settings(_chat_id(update))
    lines = [f"{key}: {value}" for key, value in sorted(data.items()) if key not in {"welcome", "goodbye", "rules"}]
    await update.message.reply_text("\n".join(lines))


async def backupsettings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    path = Path("data/backups") / f"settings-{_chat_id(update)}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(store.all_settings(_chat_id(update)), indent=2), encoding="utf-8")
    await update.message.reply_document(path.open("rb"), filename=path.name)


async def restoresettings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    await update.message.reply_text("Attach a JSON settings backup in Telegram and restore manually on the server for now.")


async def grouplink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    link = await context.bot.export_chat_invite_link(_chat_id(update))
    await update.message.reply_text(link)


async def chatstats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top = store.top_active(_chat_id(update), 5)
    total = sum(row["message_count"] for row in top)
    await update.message.reply_text(f"Tracked top-5 messages: {total}\nUse /mostactive for details.")


async def mostactive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = store.top_active(_chat_id(update), 10)
    text = "\n".join(f"{row['user_id']}: {row['message_count']} messages" for row in rows) or "No activity tracked yet."
    await update.message.reply_text(text)


async def inactive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = store.inactive(_chat_id(update), 30, 10)
    text = "\n".join(f"{row['user_id']}: last seen {row['last_seen']}" for row in rows) or "No inactive tracked users."
    await update.message.reply_text(text)


async def activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await mostactive(update, context)


async def trends(update: Update, context: ContextTypes.DEFAULT_TYPE):
    counts = store.security_counts(_chat_id(update), 24 * 60)
    await update.message.reply_text(f"24h security trend: {counts or 'quiet'}")


async def reputation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await resolve_target(update, context)
    uid = target.user_id if target else _actor_id(update)
    with store.connect() as conn:
        actions = conn.execute("SELECT COUNT(*) AS c FROM mod_logs WHERE chat_id = ? AND target_id = ?", (_chat_id(update), uid)).fetchone()["c"]
    score = max(0, 100 - actions * 10)
    await update.message.reply_text(f"Reputation for {uid}: {score}/100")


async def userinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await resolve_target(update, context)
    uid = target.user_id if target else _actor_id(update)
    await update.message.reply_text(f"User ID: {uid}\nName: {target.display_name if target else update.effective_user.full_name}")


async def id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Chat ID: {_chat_id(update)}\nUser ID: {_actor_id(update)}")


async def joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Telegram bots cannot reliably read historical join dates unless tracked from when the bot joined.")


async def avatar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await resolve_target(update, context)
    uid = target.user_id if target and target.user_id else _actor_id(update)
    photos = await context.bot.get_user_profile_photos(uid, limit=1)
    if photos.total_count == 0:
        await update.message.reply_text("No avatar found.")
        return
    await update.message.reply_photo(photos.photos[0][-1].file_id)


async def warnings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Use /warns to view warning counts.")


async def rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Rank is based on tracked activity. Use /mostactive.")


async def invites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Invite attribution is tracked only when Telegram exposes invite-link context for joins.")


async def summarizechat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Chat summarization is available through /ai when AI features are enabled.")


async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Reply to text and use /ai translate this message for now.")


async def explain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Use /ai explain <topic>.")


async def rewrite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Use /ai rewrite <message>.")


async def helpme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ask an admin, or use /help for commands and /rules for group rules.")


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_owner(update):
        return
    await update.message.reply_text("Broadcast requires a configured chat registry. Owner action logged.")


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_owner(update):
        return
    await update.message.reply_text("Restart requested. Let your process manager restart the bot after manual stop.")


async def reload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_owner(update):
        return
    await update.message.reply_text("Configuration reload requested. Restart is recommended for environment changes.")


async def errors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_owner(update):
        return
    log_path = Path("bot.log")
    await update.message.reply_text(log_path.read_text(encoding="utf-8", errors="ignore")[-3500:] if log_path.exists() else "No log file.")


async def systeminfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_owner(update):
        return
    await update.message.reply_text(f"Store DB: {store.db_path}\nTime: {datetime.utcnow().isoformat()}Z")


async def backupdb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_owner(update):
        return
    path = store.backup()
    await update.message.reply_document(path.open("rb"), filename=path.name)


async def restoredb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_owner(update):
        return
    await update.message.reply_text("For safety, restore database backups manually while the bot is stopped.")


async def maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_owner(update):
        return
    value = context.args[0].lower() in {"on", "true", "1"} if context.args else True
    store.set_setting(_chat_id(update), "maintenance", value)
    await update.message.reply_text(f"Maintenance mode set to {value}.")


COMMANDS: dict[str, Any] = {
    "tempban": tempban,
    "tempmute": tempmute,
    "enough": enough,
    "history": history,
    "purge": purge,
    "purgeuser": purgeuser,
    "report": report,
    "modstats": modstats,
    "modlogs": modlogs,
    "audit": audit,
    "pin": pin,
    "unpin": unpin,
    "slowmode": slowmode,
    "tagall": tagall,
    "hidetag": hidetag,
    "guardian": guardian,
    "antispam": antispam,
    "antilink": antilink,
    "antiflood": antiflood,
    "antiemoji": antiemoji,
    "antiraid": antiraid,
    "captcha": captcha,
    "aireplies": aireplies,
    "aimode": aimode,
    "aicooldown": aicooldown,
    "verify": verify,
    "unverify": unverify,
    "scan": scan,
    "security": security,
    "testsecurity": testsecurity,
    "threatlevel": threatlevel,
    "checkalt": checkalt,
    "checkalts": checkalts,
    "suspicious": suspicious,
    "rules": rules,
    "setrules": setrules,
    "welcome": welcome,
    "setwelcome": setwelcome,
    "goodbye": goodbye,
    "setgoodbye": setgoodbye,
    "notes": notes,
    "save": save,
    "get": get,
    "delete": delete,
    "settings": settings,
    "backupsettings": backupsettings,
    "restoresettings": restoresettings,
    "grouplink": grouplink,
    "chatstats": chatstats,
    "mostactive": mostactive,
    "inactive": inactive,
    "activity": activity,
    "trends": trends,
    "reputation": reputation,
    "userinfo": userinfo,
    "id": id_cmd,
    "joined": joined,
    "avatar": avatar,
    "warnings": warnings,
    "rank": rank,
    "invites": invites,
    "summarizechat": summarizechat,
    "translate": translate,
    "explain": explain,
    "rewrite": rewrite,
    "helpme": helpme,
    "broadcast": broadcast,
    "restart": restart,
    "reload": reload,
    "errors": errors,
    "systeminfo": systeminfo,
    "backupdb": backupdb,
    "restoredb": restoredb,
    "maintenance": maintenance,
}
