# Railway Deployment

1. Create a Railway project from this repository.
2. Set environment variables:
   - `TELEGRAM_TOKEN`
   - `OPENROUTER_API_KEY` if AI commands are enabled
   - `OWNER_ID=8577797097`
   - `ADMIN_IDS=comma,separated,ids`
3. Deploy with the included `Dockerfile` and `railway.json`.
4. Make sure only one deployment uses a Telegram token. Telegram polling allows
   only one active `getUpdates` consumer per bot token.

For production, rotate any token that was ever committed to git.
