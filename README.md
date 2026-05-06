# 🥃 Whisky_bot - Advanced Telegram Bot with AI

A production-ready Telegram bot with AI integration, advanced moderation tools, and user statistics.

## 🚀 Features

### User Features
- **🤖 AI Chat** - Ask Gemini AI anything using `/ai <question>`
- **📊 User Stats** - Track your messages and AI queries with `/stats`
- **🚫 Auto-moderation** - NSFW content filtering

### Admin Features
- **⚠️ Warning System** - Warn users, auto-ban after max warnings
- **🔇 Mute/Unmute** - Temporarily silence users (10 min default)
- **👢 Kick** - Remove users from chat
- **🚫 Ban/Unban** - Permanently ban users
- **📋 Warning Management** - Check and clear user warnings
- **👥 User Tracking** - Monitor user activity and statistics

### Technical Features
- 📝 **Persistent Storage** - Data survives bot restarts
- 📊 **Logging** - Comprehensive logging to file and console
- 🔐 **Security** - Environment variables for sensitive data
- ⚡ **Error Handling** - Robust error handling throughout
- 🎯 **Decorators** - Reusable admin/reply validation
- 🔄 **Async/Await** - Fully asynchronous operations

## 📋 Requirements

- Python 3.8+
- Telegram Bot Token (get from [@BotFather](https://t.me/botfather))
- Google Gemini API Key (get from [Google AI Studio](https://aistudio.google.com))

## 🔧 Installation

1. **Clone/Download the project**
```bash
cd Wh1sky_bot
```

2. **Create a virtual environment**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Mac/Linux
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env and add your tokens:
# TELEGRAM_TOKEN=your_token_here
# GEMINI_API_KEY=your_api_key_here
```

5. **Run the bot**
```bash
python main.py
```

## 📖 Commands

### Regular Users
| Command | Description |
|---------|------------|
| `/start` | Start the bot |
| `/help` | Show all commands |
| `/ai <question>` | Ask Gemini AI |
| `/stats` | View your statistics |

### Admin Commands
| Command | Description |
|---------|------------|
| `/warn` | Warn a user (reply to message) |
| `/warns` | Check user warnings (reply to message) |
| `/clear_warns` | Clear user warnings (reply to message) |
| `/mute` | Mute user for 10 minutes (reply to message) |
| `/unmute` | Unmute a user (reply to message) |
| `/kick` | Kick user from chat (reply to message) |
| `/ban` | Ban a user permanently (reply to message) |
| `/unban` | Unban a user (reply to message) |

## 📁 Project Structure

```
Wh1sky_bot/
├── main.py              # Main bot code
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
├── bot_data.json       # Persistent data (auto-created)
├── bot.log             # Log file (auto-created)
└── README.md           # This file
```

## 🗄️ Data Storage

Bot data is stored in `bot_data.json`:
- **Warnings**: User warning counts
- **Stats**: User message and AI query counts
- **Mutes**: Mute tracking

Data persists between bot restarts!

## 📝 Logging

Logs are saved to `bot.log` and console output includes:
- User actions
- Admin commands
- Errors and warnings
- Bot startup/shutdown

## 🔒 Security Best Practices

1. **Never commit `.env` file** - Use `.env.example` as template
2. **Rotate tokens regularly** - Update tokens in environment variables
3. **Limit admin access** - Only add trusted user IDs to `ADMIN_IDS`
4. **Monitor logs** - Check `bot.log` for suspicious activity
5. **Use secrets manager** - In production, use proper secret management

## ⚙️ Configuration

Edit settings in `main.py`:
```python
BAD_WORDS = ["porn", "sex", "xxx", "nude", "18+"]
MAX_WARNINGS = 3
MUTE_DURATION = 10  # minutes
ADMIN_IDS = [your_id_1, your_id_2]
```

## 🐛 Troubleshooting

**Bot not responding:**
- Check bot token is correct
- Verify bot has proper permissions in chat
- Check logs in `bot.log`

**AI not working:**
- Verify Gemini API key is correct
- Check API quota/limits
- Review error logs

**Commands not working:**
- Ensure you're in the right chat
- Admin commands require admin status
- Check `/help` for command syntax

## 📦 Dependencies

- `python-telegram-bot` - Telegram API wrapper
- `google-generativeai` - Gemini AI API
- `python-dotenv` - Environment variable management

## 🚀 Deployment

For production:

1. **Use a process manager** (systemd, supervisor, pm2)
2. **Set up proper logging rotation** 
3. **Use environment secrets** (not in code)
4. **Regular backups** of `bot_data.json`
5. **Monitor bot health** and uptime

Example systemd service:
```ini
[Unit]
Description=Whisky_bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/Wh1sky_bot
EnvironmentFile=/path/to/Wh1sky_bot/.env
ExecStart=/path/to/Wh1sky_bot/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 📄 License

Created for Telegram bot development.

## 👨‍💻 Author

Whisky_bot - Advanced AI Telegram Bot

---

**Need help?** Check the logs in `bot.log` for detailed error messages!
