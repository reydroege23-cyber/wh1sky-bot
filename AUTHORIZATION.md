## AUTHORIZATION SYSTEM - USER ACCESS CONTROL

### ✅ Overview

The bot now has a complete authorization system that allows admins to control which users can access the bot. By default, only admins can use the bot unless they explicitly authorize other users.

### 🔐 How It Works

**Authorization Levels:**
1. **Admins** - Full access, can authorize/deauthorize users, all commands available
2. **Authorized Users** - Granted access by admins, can use bot commands
3. **Unauthorized Users** - Blocked, get rejection message

**Protected Commands:**
- All user commands require authorization
- `/start` and `/help` are accessible without authorization (entry points)
- `/ping` is accessible without authorization
- Admin commands require admin status (authorization not needed)

### 👤 Admin Commands

**Authorize a user:**
```
Reply to user's message: /authorize
Response: ✅ Username is now authorized to use the bot!
```

**Deauthorize a user:**
```
Reply to user's message: /deauthorize
Response: 🚫 Username is no longer authorized
```

**View all authorized users:**
```
/authorized
Response: Shows list of all user IDs with access
```

### 📊 Example Workflow

**Scenario: User wants to use the bot**

1. User sends `/start` → Gets welcome message
2. User tries `/stats` → ❌ "You are not authorized"
3. Admin sees user ID and runs: `/authorize` (reply to user's message)
4. User tries `/stats` again → ✅ Works!
5. Admin can later block user with: `/deauthorize` (reply to user's message)

### 🔍 Check Authorization Status

**View all authorized users:**
- Command: `/authorized` (admin only)
- Shows list with:
  - User IDs
  - Total count

**View specific user:**
- Command: `/info` (reply to their message)
- Shows stats including warnings/authorization status

### 📁 Data Storage

Authorization data is stored in `bot_data.json`:

```json
{
    "metadata": {
        "authorized_users": [
            123456789,
            987654321
        ],
        "speak_mode": false
    }
}
```

### 🚫 Unauthorized Access

When an unauthorized user tries to use a command:

```
❌ You are not authorized to use this bot.
Contact an admin for access.
```

This applies to:
- `/stats` - View statistics
- `/roll`, `/coin`, `/dice` - Fun commands
- `/calc`, `/echo` - Utility commands
- `/ai` - Ask Whisky AI
- All other user commands

### 🔑 Protected Commands List

**Fun Commands:**
- /roll, /coin, /dice, /8ball, /flip, /reverse, /morse, /random, /fact

**Utility Commands:**
- /calc, /echo, /time, /b64, /quote

**Profile Commands:**
- /stats, /userid, /profile, /invite, /members, /uptime

**Special Commands:**
- /hajhanm, /hoba, /Serok, /Amanj, /Arya, /kurdishezdi, /Whisky

**Admin Commands:**
- Protected by @admin_only decorator (authorization not needed for admins)

### ⚙️ Configuration

Edit `config.py` to adjust authorization settings if needed. Authorization data is managed through commands, not config file.

### 🛠️ Admin Workflow

**Quick Setup - Authorize a group:**
```
1. User joins bot
2. They try a command → get rejected
3. Admin replies to any user message: /authorize
4. User now has access
5. Repeat for each user
6. OR use /authorized to see who has access
```

**Bulk Operations:**
- To remove multiple users: Reply to each message with `/deauthorize`
- No batch commands available (for security)

### 📝 Logging

Authorization events are logged to `logs.log`:

```
✅ Username (123456789) authorized
🚫 Username (123456789) deauthorized
🚫 Unauthorized bot access attempt by 987654321
✅ Authorized list viewed - 5 users
```

### 🔒 Security Notes

- Only admins can authorize/deauthorize users
- Admins have full access (cannot be restricted)
- Authorization is enforced on all user-facing commands
- Message handler checks authorization before processing
- Each command has authorization check

### ❓ Common Tasks

**Task: Give access to a new user**
```
1. User sends any message
2. Admin: Reply with /authorize
3. Done ✅
```

**Task: Remove access**
```
1. Find user's message (if available)
2. Admin: Reply with /deauthorize
3. User now blocked ✅
```

**Task: Check who has access**
```
Admin: /authorized
→ Shows all user IDs with access
```

**Task: See user stats (admin)**
```
Admin: Reply to user message with /info
→ Shows detailed stats + warning count
```

### 🆘 Troubleshooting

**Issue: "User says they can't use commands"**
- Check `/authorized` to see if they're listed
- Use `/authorize` (reply to their message) to grant access

**Issue: "User has access but gets blocked message"**
- Check that user ID is in authorized_users list
- Restart bot to reload data
- Check logs.log for errors

**Issue: "Admin can't authorize users"**
- Check admin is in ADMIN_IDS in config.py
- Verify admin is using `/authorize` with reply to user message
- Check logs.log for error messages

**Issue: "Data not saving"**
- Check disk space
- Verify bot_data.json has write permissions
- Check logs.log for "Error saving data" messages
