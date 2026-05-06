# 🥃 WHISKY_BOT - 24/7 OPERATION SETUP

## ⚡ 24/7 CONTINUOUS OPERATION

Your bot is now configured for **non-stop operation** with:
- ✅ Auto-recovery on errors
- ✅ Automatic reconnection
- ✅ Exponential backoff retry
- ✅ Graceful shutdown
- ✅ Error logging

---

## 🚀 WINDOWS SETUP (24/7)

### Option 1: Run in Background (Simple)

Create `run_bot.bat`:
```batch
@echo off
cd %~dp0
:restart
python main.py
echo.
echo Bot crashed, restarting in 5 seconds...
timeout /t 5
goto restart
```

Run: `run_bot.bat`

### Option 2: Windows Service (Advanced)

1. **Install NSSM** (Non-Sucking Service Manager):
```bash
# Download from: https://nssm.cc/download
# Extract nssm.exe to your bot folder
```

2. **Create Service**:
```bash
nssm install WhiskyBot "C:\path\to\python.exe" "C:\path\to\main.py"
nssm set WhiskyBot AppDirectory "C:\path\to\Wh1sky_bot"
nssm set WhiskyBot AppStdout "C:\path\to\Wh1sky_bot\bot.log"
nssm set WhiskyBot AppStderr "C:\path\to\Wh1sky_bot\bot.log"
```

3. **Start Service**:
```bash
nssm start WhiskyBot
nssm status WhiskyBot
```

### Option 3: Task Scheduler (Easy)

1. Create `run_forever.bat`:
```batch
@echo off
:loop
python main.py
timeout /t 10
goto loop
```

2. Open Task Scheduler:
   - New Task
   - Name: "Whisky Bot"
   - Trigger: "At startup"
   - Action: Run `run_forever.bat`
   - Check: "Run whether user is logged in or not"

---

## 🐧 LINUX/MAC SETUP (24/7)

### Option 1: Systemd Service (Recommended)

Create `/etc/systemd/system/whisky-bot.service`:

```ini
[Unit]
Description=Whisky Bot 24/7 Service
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Wh1sky_bot
EnvironmentFile=/home/pi/Wh1sky_bot/.env
ExecStart=/home/pi/Wh1sky_bot/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Enable and Start**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable whisky-bot
sudo systemctl start whisky-bot
sudo systemctl status whisky-bot
```

**Monitor**:
```bash
# View logs
sudo journalctl -u whisky-bot -f

# Check status
sudo systemctl status whisky-bot

# Restart
sudo systemctl restart whisky-bot

# Stop
sudo systemctl stop whisky-bot
```

### Option 2: Supervisor (Alternative)

Create `/etc/supervisor/conf.d/whisky-bot.conf`:

```ini
[program:whisky-bot]
command=/home/pi/Wh1sky_bot/venv/bin/python /home/pi/Wh1sky_bot/main.py
directory=/home/pi/Wh1sky_bot
user=pi
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/pi/Wh1sky_bot/bot.log
environment=PATH="/home/pi/Wh1sky_bot/venv/bin"
```

**Enable and Start**:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start whisky-bot
sudo supervisorctl status
```

### Option 3: Screen/Tmux (Simple)

```bash
# Using screen
screen -S whisky-bot -d -m python main.py

# Using tmux
tmux new-session -d -s whisky-bot "python main.py"

# Attach to check
screen -r whisky-bot
tmux attach-session -t whisky-bot
```

### Option 4: Cron Job (Restart Daily)

```bash
# Edit crontab
crontab -e

# Add these lines:
# Restart bot daily at 2 AM
0 2 * * * /home/pi/Wh1sky_bot/restart_bot.sh

# Check status every hour
0 * * * * /home/pi/Wh1sky_bot/check_bot.sh
```

Create `restart_bot.sh`:
```bash
#!/bin/bash
pkill -f "python main.py"
sleep 2
cd /home/pi/Wh1sky_bot
python main.py &
```

---

## 🐳 DOCKER SETUP (24/7)

Create `Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

**Build and Run**:
```bash
# Build
docker build -t whisky-bot .

# Run (24/7)
docker run -d \
  --name whisky-bot \
  --env-file .env \
  --restart unless-stopped \
  --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  whisky-bot

# View logs
docker logs -f whisky-bot

# Status
docker ps | grep whisky-bot

# Stop/Start
docker stop whisky-bot
docker start whisky-bot
```

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  whisky-bot:
    build: .
    restart: unless-stopped
    env_file: .env
    volumes:
      - ./bot.log:/app/bot.log
      - ./bot_data.json:/app/bot_data.json
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

**Run with Docker Compose**:
```bash
docker-compose up -d
docker-compose logs -f
docker-compose down
```

---

## 📊 MONITORING (24/7)

### Check Bot Status Script

Create `check_bot.sh`:
```bash
#!/bin/bash

# Check if bot is running
if pgrep -f "python main.py" > /dev/null; then
    echo "✅ Bot is running"
else
    echo "❌ Bot is NOT running"
    echo "🔄 Starting bot..."
    cd /home/pi/Wh1sky_bot
    python main.py &
fi

# Check bot data size
BOT_DATA_SIZE=$(stat -f%z bot_data.json 2>/dev/null || stat -c%s bot_data.json 2>/dev/null)
echo "📊 Bot data: ${BOT_DATA_SIZE} bytes"

# Check log size
LOG_SIZE=$(stat -f%z bot.log 2>/dev/null || stat -c%s bot.log 2>/dev/null)
echo "📝 Log file: ${LOG_SIZE} bytes"

# Show last 5 errors
echo "🔍 Recent errors:"
grep "ERROR\|❌\|🔥" bot.log | tail -5
```

### Auto-Restart Script

Create `auto_restart.sh`:
```bash
#!/bin/bash

while true; do
    if ! pgrep -f "python main.py" > /dev/null; then
        echo "$(date) - Bot crashed, restarting..." >> bot_restart.log
        cd /home/pi/Wh1sky_bot
        python main.py &
    fi
    sleep 60  # Check every minute
done
```

---

## 🔧 MAINTENANCE (24/7 Operation)

### Daily Tasks

```bash
# Backup data
cp bot_data.json bot_data.json.backup

# Check logs
tail -100 bot.log | grep ERROR

# Monitor memory
ps aux | grep python | grep main.py
```

### Weekly Tasks

```bash
# Archive old logs
cp bot.log bot.log.$(date +%Y%m%d)
> bot.log  # Clear log

# Check disk space
df -h

# Verify backups
ls -lah bot_data.json*
```

### Monthly Tasks

```bash
# Full backup
tar -czf whisky-bot-backup-$(date +%Y%m%d).tar.gz \
    bot_data.json bot.log config.py

# Update dependencies
pip install --upgrade -r requirements.txt

# Review logs for issues
grep "ERROR" bot.log | wc -l
```

---

## 📈 AUTO-RECOVERY FEATURES

Your bot now has:

✅ **Automatic Reconnection**
   - Detects connection loss
   - Retries with exponential backoff
   - Max 5 retries (up to 5 minutes)

✅ **Error Logging**
   - All errors logged to `bot.log`
   - File rotation recommended
   - Easy troubleshooting

✅ **Graceful Shutdown**
   - Saves data before exit
   - Proper cleanup
   - Ready for restart

✅ **Message Queue**
   - `drop_pending_updates=True` prevents message buildup
   - Fresh start after restart
   - No duplicate processing

---

## 🚨 TROUBLESHOOTING 24/7

### Bot Keeps Crashing

```bash
# Check logs
tail -50 bot.log

# Check Python version
python --version

# Verify dependencies
pip list | grep -E "telegram|generativeai"

# Test manually
python -c "import main; print('✅ OK')"
```

### High Memory Usage

```bash
# Monitor memory
watch -n 1 'ps aux | grep main.py'

# Kill and restart
pkill -f "python main.py"
python main.py &
```

### Network Issues

```bash
# Check internet
ping -c 3 8.8.8.8

# Check DNS
nslookup api.telegram.org

# Restart network
# Linux: sudo systemctl restart networking
# Mac: sudo ifconfig en0 down && sleep 2 && sudo ifconfig en0 up
```

### Log File Too Large

```bash
# Check size
du -h bot.log

# Rotate logs
mv bot.log bot.log.old
# Bot will create new bot.log automatically

# Archive old
gzip bot.log.old
```

---

## 📋 24/7 CHECKLIST

- [ ] Selected operation method (systemd/Docker/Screen/etc)
- [ ] Created configuration file
- [ ] Set auto-restart enabled
- [ ] Verified .env file exists
- [ ] Tested manual start: `python main.py`
- [ ] Set up monitoring/logging
- [ ] Configured backup strategy
- [ ] Set up daily/weekly maintenance
- [ ] Documented restart procedure
- [ ] Tested restart after crash

---

## 🎯 QUICK START GUIDES

### Windows (Simplest)
```batch
@echo off
:loop
python main.py
timeout /t 10
goto loop
```

### Linux (Systemd)
```bash
sudo cp whisky-bot.service /etc/systemd/system/
sudo systemctl enable whisky-bot
sudo systemctl start whisky-bot
```

### Docker (Modern)
```bash
docker-compose up -d
```

### Raspberry Pi (Easy)
```bash
# Add to crontab
@reboot /home/pi/Wh1sky_bot/start_bot.sh
```

---

## 📞 SUPPORT

If bot keeps crashing:
1. Check `bot.log` for errors
2. Run `python validate.py`
3. Verify internet connection
4. Check Python/dependency versions
5. Increase retry delay in `config.py`

If you need to stop:
- **Windows**: Close terminal or `Ctrl+C`
- **Linux**: `sudo systemctl stop whisky-bot`
- **Docker**: `docker-compose down`

---

## 🎉 NOW 24/7 READY!

Your bot is configured for:
- ✅ Continuous operation
- ✅ Auto-recovery
- ✅ Error handling
- ✅ Proper logging
- ✅ Easy monitoring

Choose your platform above and follow the setup instructions!

**Status**: 🟢 **24/7 READY**
