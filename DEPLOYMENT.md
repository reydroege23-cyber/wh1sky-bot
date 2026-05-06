# 🥃 WHISKY_BOT ELITE - DEPLOYMENT GUIDE

## ✅ PRE-DEPLOYMENT CHECKLIST

### Step 1: Environment Setup
- [ ] Python 3.8+ installed
- [ ] `requirements.txt` installed
- [ ] `.env` file created
- [ ] `TELEGRAM_TOKEN` set
- [ ] `GEMINI_API_KEY` set

### Step 2: Validation
```bash
python validate.py
```
- [ ] All files present
- [ ] No syntax errors
- [ ] Config valid
- [ ] All imports work
- [ ] Database functional

### Step 3: Testing
```bash
python test_bot.py
```
- [ ] All tests pass
- [ ] No warnings
- [ ] Code quality OK

### Step 4: Configuration
- [ ] Admin IDs set correctly
- [ ] Bad words list updated (if needed)
- [ ] Max warnings set (default: 3)
- [ ] Mute duration set (default: 10 min)

### Step 5: Documentation
- [ ] README.md read
- [ ] FEATURES.md reviewed
- [ ] QUICKSTART.md understood

---

## 🚀 RUNNING THE BOT

### Local Development
```bash
python main.py
```

Expected output:
```
============================================================
🥃 WHISKY_BOT - ELITE VERSION STARTING
👮 Admin IDs: [...]
🤖 AI Status: ✅ ONLINE
📊 Tracking X users
============================================================

✅ Bot is running... Press Ctrl+C to stop
```

### Test the Bot
1. Send `/start` to your bot
2. Send `/help` to see commands
3. Send `/ping` to check status
4. Send `/ai hello` to test AI

---

## 🐳 PRODUCTION DEPLOYMENT

### Option 1: System Service (Linux/Mac)

Create `/etc/systemd/system/whisky-bot.service`:
```ini
[Unit]
Description=Whisky_bot Telegram Bot
After=network.target

[Service]
Type=simple
User=whisky
WorkingDirectory=/home/whisky/whisky_bot
EnvironmentFile=/home/whisky/whisky_bot/.env
ExecStart=/home/whisky/whisky_bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable whisky-bot
sudo systemctl start whisky-bot
sudo systemctl status whisky-bot
```

### Option 2: Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

Build and run:
```bash
docker build -t whisky-bot .
docker run -d --env-file .env whisky-bot
```

### Option 3: Screen/Tmux

Using screen:
```bash
screen -S whisky-bot
python main.py
# Press Ctrl+A then D to detach
```

Using tmux:
```bash
tmux new-session -d -s whisky-bot python main.py
```

---

## 📊 MONITORING

### Check Bot Status
```bash
# Check if running
ps aux | grep main.py

# Check logs
tail -f bot.log

# Count users
cat bot_data.json | grep messages
```

### Common Issues

**Bot not starting:**
```bash
python validate.py  # Check configuration
python test_bot.py  # Run tests
tail bot.log        # Check errors
```

**AI not working:**
- Verify Gemini API key
- Check API quota
- Review error logs

**High memory usage:**
- Check bot_data.json size
- Archive old data
- Restart bot

---

## 🔄 MAINTENANCE

### Regular Tasks
- **Daily**: Check logs for errors
- **Weekly**: Backup bot_data.json
- **Monthly**: Review admin actions
- **Quarterly**: Update dependencies

### Backup Procedure
```bash
# Backup data
cp bot_data.json bot_data.json.backup

# Backup logs
cp bot.log bot.log.backup

# Archive old data
tar -czf whisky-bot-backup-$(date +%Y%m%d).tar.gz \
    bot_data.json bot.log config.py
```

### Update Procedure
```bash
# Stop bot
# Ctrl+C or: systemctl stop whisky-bot

# Backup current state
cp bot_data.json bot_data.json.backup

# Pull latest code
git pull  # or download manually

# Install updates
pip install -r requirements.txt

# Start bot
python main.py  # or: systemctl start whisky-bot
```

---

## 🔐 SECURITY BEST PRACTICES

### API Keys
- ✅ Use `.env` file
- ✅ Never commit `.env`
- ✅ Rotate keys regularly
- ✅ Use different keys per environment

### Admin Access
- ✅ Limit admin count
- ✅ Monitor admin actions
- ✅ Verify admin permissions
- ✅ Log all admin commands

### Data Protection
- ✅ Regular backups
- ✅ Encrypted storage (optional)
- ✅ Access control
- ✅ Audit logs

### Bot Security
- ✅ Update dependencies
- ✅ Monitor for vulnerabilities
- ✅ Use HTTPS (Telegram handles this)
- ✅ Rate limiting (built-in)

---

## 📈 SCALING

### Single Bot
- Up to 10,000 users
- One server
- No database needed
- Simple deployment

### Multiple Bots
- Load balancing
- Shared database
- Distributed logging
- API gateway

### Advanced Setup
- Kubernetes cluster
- Redis caching
- PostgreSQL database
- Prometheus monitoring

---

## 🆘 TROUBLESHOOTING

### Bot Won't Start
```bash
# Check Python version
python --version

# Check dependencies
pip list | grep -E 'telegram|generativeai'

# Validate syntax
python -m py_compile main.py

# Run validation
python validate.py
```

### Commands Not Working
- Check admin permissions
- Verify reply requirement met
- Check error logs
- Test with `/help`

### AI Timeouts
- Longer prompts = slower response
- Check internet connection
- Verify API key valid
- Check API rate limits

### Data Loss
- Check bot_data.json exists
- Verify file permissions
- Check disk space
- Restore from backup

---

## 📞 SUPPORT RESOURCES

### Documentation
- 📖 README.md - Full guide
- ⚡ QUICKSTART.md - Quick setup
- ✨ FEATURES.md - All features
- 🚀 This file - Deployment

### Tools
- 🧪 test_bot.py - Testing suite
- ✅ validate.py - Validation tool
- 📝 bot.log - Error logs
- 💾 bot_data.json - User data

### External Help
- 📚 [Telegram Bot API](https://core.telegram.org/bots/api)
- 🤖 [Google Gemini API](https://ai.google.dev)
- 🐍 [Python Telegram Bot](https://python-telegram-bot.org)

---

## 🎯 PERFORMANCE TIPS

### Optimization
1. Use faster API calls
2. Cache frequently accessed data
3. Limit background tasks
4. Monitor memory usage
5. Clean up old logs

### Monitoring
1. Track response times
2. Monitor error rates
3. Check resource usage
4. Analyze user patterns
5. Review logs regularly

### Improvement
1. Update dependencies monthly
2. Profile code for bottlenecks
3. Optimize database queries
4. Reduce API calls
5. Cache responses

---

## 📋 DEPLOYMENT CHECKLIST

- [ ] Environment variables set
- [ ] Validation passes
- [ ] Tests pass
- [ ] Bot starts without errors
- [ ] Commands respond
- [ ] AI works
- [ ] Admins can moderate
- [ ] Logging works
- [ ] Data persists
- [ ] Monitoring in place
- [ ] Backups configured
- [ ] Documentation reviewed

---

## 🎉 READY FOR PRODUCTION!

Your **Whisky_bot Elite** is now production-ready. Follow this guide for smooth deployment and maintenance.

**Questions?** Check the logs and documentation.

**Having issues?** Run `python validate.py` and `python test_bot.py`.

Good luck! 🚀
