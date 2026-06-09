"""Telegram command menu synchronization.

Telegram's slash suggestions are controlled by Bot API command menus, not by
CommandHandler registration alone. Keep this file as the single source of truth
for commands that should appear when users type "/".
"""

from __future__ import annotations

import logging

from telegram import (
    BotCommand,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeDefault,
)
from telegram.ext import Application


logger = logging.getLogger(__name__)


PRIVATE_COMMANDS = [
    BotCommand("start", "Start the bot"),
    BotCommand("help", "Show help menu"),
    BotCommand("ping", "Check bot latency"),
    BotCommand("stats", "Bot statistics"),
    BotCommand("ai", "Ask Marine AI"),
    BotCommand("rules", "Show group rules"),
    BotCommand("settings", "View group settings"),
    BotCommand("exportsettings", "Export this chat settings"),
    BotCommand("importsettings", "Import this chat settings"),
    BotCommand("panel", "Open Marine admin panel"),
    BotCommand("cmds", "Show all commands"),
    BotCommand("marine", "Show Marine capabilities"),
]


GROUP_COMMANDS = [
    BotCommand("help", "Show help menu"),
    BotCommand("rules", "Show group rules"),
    BotCommand("setrules", "Set group rules"),
    BotCommand("welcome", "Show welcome message"),
    BotCommand("setwelcome", "Set welcome message"),
    BotCommand("goodbye", "Show goodbye message"),
    BotCommand("setgoodbye", "Set goodbye message"),
    BotCommand("report", "Report a user"),
    BotCommand("admins", "List admins"),
    BotCommand("ban", "Ban a user"),
    BotCommand("unban", "Unban a user"),
    BotCommand("kick", "Kick a user"),
    BotCommand("mute", "Mute a user"),
    BotCommand("unmute", "Unmute a user"),
    BotCommand("tempban", "Temporarily ban a user"),
    BotCommand("tempmute", "Temporarily mute a user"),
    BotCommand("warn", "Warn a user"),
    BotCommand("warns", "View warnings"),
    BotCommand("clearwarns", "Clear warnings"),
    BotCommand("enough", "Permanently re-ban a user"),
    BotCommand("guardian", "Enable emergency protection"),
    BotCommand("antispam", "Configure anti-spam"),
    BotCommand("antilink", "Configure anti-link"),
    BotCommand("antiflood", "Configure anti-flood"),
    BotCommand("antiemoji", "Configure anti-emoji"),
    BotCommand("antiraid", "Configure anti-raid"),
    BotCommand("scan", "Scan group security"),
    BotCommand("security", "Show security status"),
    BotCommand("testsecurity", "Test security scanner"),
    BotCommand("threatlevel", "Show threat level"),
    BotCommand("checkalt", "Check suspicious alt risk"),
    BotCommand("modlogs", "View moderation logs"),
    BotCommand("modstats", "View moderation stats"),
    BotCommand("audit", "Audit protection settings"),
    BotCommand("settings", "View group settings"),
    BotCommand("resetsettings", "Reset this chat settings"),
    BotCommand("exportsettings", "Export this chat settings"),
    BotCommand("importsettings", "Import this chat settings"),
    BotCommand("copysettings", "Owner-only settings copy"),
    BotCommand("panel", "Open Marine admin panel"),
    BotCommand("toggle", "Toggle protection features"),
    BotCommand("cmds", "Show all commands"),
    BotCommand("logs", "Show recent logs"),
    BotCommand("chatstats", "View chat statistics"),
    BotCommand("mostactive", "Show most active users"),
    BotCommand("marine", "Show Marine capabilities"),
]


DEFAULT_COMMANDS = PRIVATE_COMMANDS


def command_names() -> set[str]:
    """Return every command name exposed through Telegram menus."""
    return {command.command for command in [*DEFAULT_COMMANDS, *PRIVATE_COMMANDS, *GROUP_COMMANDS]}


async def sync_bot_commands(application: Application) -> None:
    """Synchronize Telegram slash-command menus on every bot startup."""
    scopes = [
        ("default", BotCommandScopeDefault(), DEFAULT_COMMANDS),
        ("private", BotCommandScopeAllPrivateChats(), PRIVATE_COMMANDS),
        ("groups", BotCommandScopeAllGroupChats(), GROUP_COMMANDS),
    ]

    for scope_name, scope, commands in scopes:
        try:
            logger.info(
                "Synchronizing %s Telegram command menu with %d commands: %s",
                scope_name,
                len(commands),
                ", ".join(f"/{command.command}" for command in commands),
            )
            await application.bot.set_my_commands(commands=commands, scope=scope)
            logger.info("Telegram command menu synchronized for %s scope", scope_name)
        except Exception:
            logger.exception("Failed to synchronize Telegram command menu for %s scope", scope_name)
