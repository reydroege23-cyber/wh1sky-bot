# Architecture Overview

The bot now keeps the legacy command surface while adding a modular production
foundation:

- `main.py`: Telegram application bootstrap and legacy command handlers.
- `commands/`: new command modules for group management and owner/admin tools.
- `services/`: durable SQLite services for settings, logs, analytics, security events, and permanent bans.
- `data/`: SQLite databases and generated backups.
- `logs/`: reserved for runtime logs.
- `tests/`: automated tests for service and safety logic.

The current migration strategy is incremental: new production features are
implemented as modules and registered from `main.py`, avoiding a risky all-at-once
rewrite of the existing bot.
