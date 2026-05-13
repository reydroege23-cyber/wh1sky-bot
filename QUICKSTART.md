# 🚀 QUICK START GUIDE - WHISKY BOT ELITE

## ⚡ 30-Second Setup

### 1️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 2️⃣ Configure Bot
Create `.env` file:
```
TELEGRAM_TOKEN=your_token_here
OPENROUTER_API_KEY=your_key_here
```

Get tokens from:
- **Telegram**: [@BotFather](https://t.me/botfather)
- **Whisky AI**: [OpenRouter](https://openrouter.ai/keys)

### 3️⃣ Run Bot
```bash
python main.py
```

✅ Done! Bot is running.

---

## 🧪 Testing

Run the test suite:
```bash
python test_bot.py
```

---

## 📋 ELITE FEATURES

### 🤖 AI Chat
```
/ai What is Python?
```

### 📊 Statistics
```
/stats
```

### 👮 Admin Commands
```
/warn (reply to user)
/mute (reply to user)
/ban (reply to user)
/info (reply to user)
```

### 🔧 Configuration
Edit `config.py` to customize:
- Admin IDs
- Bad words
- Max warnings
- Mute duration

---

## 🐛 Troubleshooting

### Bot not starting?
- Check `.env` file has correct tokens
- Run: `python test_bot.py`
- Check `bot.log` for errors

### AI not working?
- Verify OpenRouter API key
- Check API quota
- Review error logs

### Commands not working?
- Ensure you're replying to correct message
- Check admin permissions
- Verify command syntax

---

## 📁 Project Structure

```
Wh1sky_bot/
├── main.py              # Bot code
├── config.py            # Settings
├── requirements.txt     # Dependencies
├── test_bot.py          # Test suite
├── .env                 # Secrets (create this)
├── .env.example         # Template
├── bot.log              # Logs (auto-created)
├── bot_data.json        # Data (auto-created)
└── README.md            # Full docs
```

---

## ✨ ELITE VERSION FEATURES

✅ **14+ Commands** - Comprehensive moderation
✅ **AI Integration** - Whisky AI (OpenRouter)
✅ **User Tracking** - Statistics & history
✅ **Persistent Data** - Survives restarts
✅ **Admin System** - Multi-admin support
✅ **Error Handling** - Robust & graceful
✅ **Logging** - Full audit trail
✅ **Decorators** - Clean code
✅ **Production Ready** - Battle-tested

---

## 🎯 Next Steps

1. ✅ Setup complete
2. 📝 Customize `config.py` (optional)
3. 🚀 Run the bot
4. 💬 Test with `/start` command
5. 👮 Use admin commands as needed

---

**🥃 WHISKY_BOT ELITE - Ready to serve!**
