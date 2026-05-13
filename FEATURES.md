# 🥃 WHISKY_BOT ELITE - FEATURES & CAPABILITIES

## 📊 OVERVIEW

**Whisky_bot Elite** is a production-grade Telegram bot with:
- 🤖 AI Integration (Whisky AI powered by OpenRouter)
- 👮 Advanced Moderation
- 📊 User Statistics & Tracking
- 💾 Persistent Data Storage
- 🔐 Multi-Admin System
- 📝 Comprehensive Logging
- ⚡ High Performance
- 🔄 Error Recovery

---

## 👥 USER FEATURES

### 1. AI Chat `/ai <question>`
- Ask Whisky AI anything
- Get instant responses
- Timeout protection
- Error handling
- Tracked usage stats

**Example:**
```
/ai How do I learn Python?
```

### 2. User Statistics `/stats`
- Total messages sent
- AI queries made
- Warning count
- Member since date
- Last active timestamp

**Display:**
```
📊 YOUR STATISTICS
📨 Messages: 42
🤖 AI Queries: 15
⚠️ Warnings: 0/3
📅 Member since: 2026-05-06
```

### 3. Bot Status `/ping`
- Real-time status check
- AI service status
- Response time monitoring
- Uptime tracking

### 4. Help `/help`
- Complete command reference
- Usage examples
- Configuration details
- Admin command guide

### 5. Dice Roller `/roll [sides]`
- Roll dice with custom sides
- Default: 6-sided dice
- Instant random generation
- Perfect for games

**Example:**
```
/roll 20      (20-sided dice)
/roll         (6-sided dice)
```

### 6. Coin Flip `/coin`
- Flip a coin instantly
- Heads or Tails
- Fair randomization
- Game companion

### 7. Calculator `/calc <expression>`
- Simple math calculations
- Supports: + - * / % **
- Examples: `2+2`, `10*5`, `100/2`
- Safe evaluation

**Example:**
```
/calc 2+2
/calc (10*5)+3
/calc 100/4
```

### 8. Echo `/echo <text>`
- Repeat your message
- Perfect for testing
- Text feedback
- Max 200 characters

### 9. Time `/time`
- Show current time
- UTC+0 format
- Timestamp reference
- Server time check

### 10. Welcome Message `/start`
- Personalized greeting
- Feature overview
- Quick navigation
- User logging

---

## 👮 ADMIN FEATURES

All admin commands require **replying to a user's message**.

### Warning System
- **`/warn`** - Issue warning
- **`/warns`** - Check warnings
- **`/clear_warns`** - Reset warnings
- Auto-ban after max warnings
- Persistent warning storage

### User Control
- **`/Shut`** - Silence user (10 min)
- **`/unmute`** - Restore voice
- **`/kick`** - Remove from chat
- **`/ban`** - Permanent ban
- **`/unban`** - Restore access

### Information
- **`/info`** - View user profile
- **`/admins`** - List all admins
- Real-time user statistics
- Complete audit trail

---

## 🔐 SECURITY & MODERATION

### Automatic NSFW Filtering
- Bad word detection
- Auto message deletion
- Warning system
- Case-insensitive matching
- Expandable word list

**Bad Words Detected:**
```
porn, sex, xxx, nude, 18+
```

### Admin Protection
- Cannot warn admins
- Cannot mute admins
- Cannot kick admins
- Cannot ban admins
- Unauthorized access logging

### Permission System
- Multi-admin support
- Command validation
- Reply requirement checking
- User ID validation
- Error handling

---

## 📊 STATISTICS & TRACKING

### Per-User Tracking
- Messages sent
- AI queries made
- Warning count
- First seen date
- Last activity

### Persistent Storage
- JSON-based storage
- Bot restart survival
- Easy backup
- Manual editing capability

### Metadata
- Timestamps
- User IDs
- Chat information
- Action logs

---

## 🤖 AI INTEGRATION

### Whisky AI (OpenRouter)

**Fast, Reliable LLM**
- Fast responses
- Low latency
- Cost effective
- High accuracy

### Features
- Timeout protection (10s)
- Response length limiting (4096 chars)
- Error recovery
- Offline fallback
- Query tracking

### Usage Examples
```
/ai What is AI?
/ai Write Python code for...
/ai Explain quantum computing
/ai Translate to Spanish: Hello
/ai What's the capital of France?
```

---

## 📝 LOGGING & DEBUGGING

### Log Types
- User actions
- Admin commands
- AI responses
- Error messages
- System events

### Log Destinations
- `bot.log` file
- Console output
- Real-time monitoring

### Sample Log Lines
```
2026-05-06 10:15:42 - __main__ - INFO - 👤 New user: 123456 (John)
2026-05-06 10:16:15 - __main__ - INFO - 🤖 AI query from 123456
2026-05-06 10:17:30 - __main__ - WARNING - ⚠️ User warned (2/3)
```

---

## ⚡ PERFORMANCE

### Optimization Features
- Async/await throughout
- Efficient data storage
- Minimal memory footprint
- Fast command processing
- Connection pooling

### Scalability
- Handles multiple users
- Concurrent operations
- No blocking operations
- Efficient decorators
- Smart caching

---

## 🛠️ ADVANCED FEATURES

### Decorators
1. **`@admin_only`** - Admin validation
2. **`@reply_required`** - Reply checking
3. **`@user_tracking`** - Statistics tracking

### Error Recovery
- Graceful degradation
- Offline AI fallback
- Connection recovery
- Data persistence
- Automatic retry logic

### Customization
- Config-based settings
- Expandable commands
- Custom bad words
- Flexible admin list
- Adjustable timeouts

---

## 🔧 CONFIGURATION

### Core Settings
```python
ADMIN_IDS = [123456, 789012]      # Admin user IDs
MAX_WARNINGS = 3                   # Ban threshold
MUTE_DURATION = 10                 # Minutes
AI_MODEL = "meta-llama/llama-3.1-8b-instruct"     # AI model
AI_TIMEOUT = 10                    # Seconds
```

### Content Filtering
```python
BAD_WORDS = [
    "porn", "sex", "xxx", "nude", "18+"
]
```

### Features
```python
ENABLE_STATS = True                # User tracking
ENABLE_LOGGING = True              # File logging
ENABLE_AUTO_MODERATION = True      # NSFW filter
```

---

## 📱 USER EXPERIENCE

### Clean Interface
- Emoji indicators
- Clear messages
- Helpful feedback
- Error explanations

### Command Feedback
```
✅ - Success
❌ - Error
⚠️ - Warning
🤖 - AI
👤 - User
👮 - Admin
🔇 - Mute
🔊 - Unmute
🚫 - Ban
✅ - Unban
```

### Smart Responses
- Context-aware messages
- User-friendly language
- Helpful instructions
- Error recovery

---

## 🚀 DEPLOYMENT

### Local Development
```bash
python main.py
```

### Production Ready
- Error handling
- Logging setup
- Data persistence
- Admin alerts
- Monitoring support

### System Requirements
- Python 3.8+
- 50MB disk space
- Internet connection
- Telegram account
- OpenRouter API access

---

## 🎯 COMPARISON

| Feature | Basic | Elite |
|---------|-------|-------|
| Commands | 6 | 14+ |
| AI Integration | Basic | Advanced |
| User Tracking | No | Yes |
| Logging | Limited | Comprehensive |
| Admin Features | Basic | Advanced |
| Error Handling | Basic | Robust |
| Configuration | Limited | Extensive |
| Scalability | Limited | High |
| Production Ready | No | Yes |

---

## 📞 SUPPORT

### Features Issues
- Check `bot.log`
- Review `config.py`
- Test with `/ping`
- Check admin permissions

### AI Issues
- Verify Whisky AI key
- Check API quota
- Review timeout settings
- Check internet connection

### Data Issues
- Check `bot_data.json`
- Verify file permissions
- Check disk space
- Review error logs

---

## 🎉 WHAT MAKES IT ELITE?

✨ **Production Grade Code**
✨ **Advanced Features**
✨ **Comprehensive Logging**
✨ **Error Recovery**
✨ **User Tracking**
✨ **Admin System**
✨ **AI Integration**
✨ **Persistent Storage**
✨ **Multi-Admin Support**
✨ **Security First**

---

**🥃 WHISKY_BOT ELITE - The Best Telegram Bot**
