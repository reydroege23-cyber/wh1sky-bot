# Troubleshooting

## Conflict: terminated by other getUpdates request

Another process is using the same Telegram token. Stop duplicate local terminals,
old VPS processes, or previous hosting deployments. If you cannot find the
duplicate, rotate the token in BotFather.

## Bot cannot ban or delete messages

Promote the bot to administrator and grant the required Telegram permissions.

## AI commands fail

Set `OPENROUTER_API_KEY` or disable AI-facing workflows.
