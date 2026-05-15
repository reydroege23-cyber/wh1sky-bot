# 🛡️ ADMIN COMMANDS - USER TRACKING FIX

## Overview

The admin commands `/addcoins`, `/removecoins`, and `/setcoins` now properly track users by **User ID** instead of usernames. All balances are stored and tracked using numeric user IDs internally.

## Commands

### 1. `/addcoins` - Add Coins to User

**Purpose:** Give coins to a specific user

**Syntax Options:**

**Option A: Reply Method (Most Reliable)**
```
[Reply to user's message]
/addcoins 500
```
- Reply to any message from the target user
- Then send `/addcoins 500`
- Bot automatically detects target from the replied message
- **Recommended**: This is the most reliable method

**Option B: Direct User ID**
```
/addcoins 123456789 500
```
- First argument: Target user's ID
- Second argument: Amount of coins
- Example: `/addcoins 987654321 100`

**Option C: Username (If Available)**
```
/addcoins @username 500
```
- Uses @mention format
- Bot attempts to resolve username to user ID
- Only works in groups/channels where username is known
- Falls back to error if username cannot be resolved

**Examples:**

```
# Reply method - safest
User sends: "hello"
Admin replies to that message with: /addcoins 500
Result: User gets 500 coins

# Direct ID method
/addcoins 123456789 500
Result: User 123456789 gets 500 coins
```

**Output:**
```
✅ Added 500 coins to user 123456789
💰 New balance: 1500
```

**Debug Logs:**
```
✅ Resolved user from reply: 123456789
💰 Admin 987654321 added 500 coins to 123456789. New balance: 1500
```

---

### 2. `/removecoins` - Remove Coins from User

**Purpose:** Take coins from a specific user

**Syntax Options:**

**Option A: Reply Method (Most Reliable)**
```
[Reply to user's message]
/removecoins 200
```

**Option B: Direct User ID**
```
/removecoins 123456789 200
```

**Option C: Username**
```
/removecoins @username 200
```

**Examples:**

```
# Remove 200 coins via reply
/removecoins 200

# Remove 200 coins via user ID
/removecoins 123456789 200
```

**Output:**
```
✅ Removed 200 coins from user 123456789
💰 New balance: 1300
```

**Error Handling:**
```
❌ User only has 50 coins!
Cannot remove 200
```

**Debug Logs:**
```
💰 Admin 987654321 removed 200 coins from 123456789. New balance: 1300
```

---

### 3. `/setcoins` - Set Exact Balance

**Purpose:** Set a user's balance to exact amount (admin override)

**Syntax Options:**

**Option A: Reply Method (Most Reliable)**
```
[Reply to user's message]
/setcoins 1000
```
- Sets target's balance to exactly 1000 coins

**Option B: Direct User ID**
```
/setcoins 123456789 1000
```

**Option C: Username**
```
/setcoins @username 1000
```

**Examples:**

```
# Set balance to 1000 via reply
/setcoins 1000

# Set balance to 500 via user ID
/setcoins 123456789 500

# Reset user to starting balance (100 coins)
/setcoins 123456789 100
```

**Output:**
```
✅ Set user 123456789 balance to 1000 coins
💰 Previous: 1500 → New: 1000
```

**Debug Logs:**
```
💰 Admin 987654321 set 123456789 balance from 1500 to 1000 coins
```

---

## How It Works Internally

### User Resolution Process

When you run an admin command, the bot follows this process:

```
1. Check if replying to a message
   ├─ YES → Use replied-to user's ID
   └─ NO → Go to step 2

2. Check if first argument is a number
   ├─ YES → Treat as direct user ID
   └─ NO → Go to step 3

3. Check if first argument starts with @
   ├─ YES → Try to resolve @username to ID
   │   ├─ Success → Use resolved ID
   │   └─ Fail → Send error
   └─ NO → Send error

4. Extract amount from correct argument position

5. Ensure user exists in economy (auto-create with STARTING_BALANCE)

6. Perform operation and log action

7. Show result to admin
```

### Example Flow - Reply Method

```
Step 1: User sends message "Hello bot"
        Message ID: msg_12345
        From user: 123456789

Step 2: Admin replies to that message with: /addcoins 500
        Command detected: /addcoins
        Amount: 500
        Reply detected: YES
        Target ID: 123456789 (from replied message)

Step 3: Check user 123456789 exists
        ├─ Exists: Get current balance
        └─ Doesn't exist: Create with STARTING_BALANCE (100)

Step 4: Add 500 coins
        Old balance: 100
        New balance: 600

Step 5: Log: "Admin 987654321 added 500 coins to 123456789"

Step 6: Send reply: "✅ Added 500 coins to user 123456789\n💰 New balance: 600"

Step 7: Update bot_data.json with new balance
```

### Example Flow - Direct ID Method

```
Step 1: Admin sends: /addcoins 123456789 500

Step 2: Parse command
        Amount: 500
        Target argument: 123456789

Step 3: Check if target is number
        ✅ YES - It's a number
        User ID: 123456789

Step 4-7: Same as reply method...
```

---

## Key Features

### ✅ Auto-User Creation

When you use an admin command on a new user:
1. Bot checks if user exists in economy database
2. If NOT found → Bot auto-creates profile with STARTING_BALANCE (100 coins)
3. Then applies the admin command

```python
# Example: Setting coins for new user
/setcoins 999888777 500

# Bot does:
# 1. Check if 999888777 exists → NO
# 2. Create: 999888777 with balance 100
# 3. Update: 999888777 balance to 500
```

### ✅ User ID Tracking

All balances are stored by **numeric user ID**:

```json
{
  "economy": {
    "123456789": 1000,
    "987654321": 500,
    "555666777": 250
  }
}
```

### ✅ Debug Logging

Every admin action is logged with:
- Admin user ID
- Target user ID
- Action performed
- Old balance → New balance
- Timestamp

```
✅ Resolved user from reply: 123456789
💰 Admin 987654321 added 500 coins to 123456789. New balance: 1500
```

### ✅ Error Handling

**Invalid formats:**
```
❌ Usage:
1. Reply to user + `/command amount`
2. `/command <user_id> <amount>`
```

**User not found:**
```
❌ Could not find user @username
Try replying to their message instead.
```

**Insufficient funds (remove only):**
```
❌ User only has 50 coins!
Cannot remove 200
```

**Invalid amount:**
```
❌ Amount must be a number
```

---

## Usage Examples

### Scenario 1: Reward Active Player

```
Bot group chat:
Player: "Thanks for the bot!"
Admin: [Reply to message] /addcoins 100

Result:
✅ Added 100 coins to user 123456789
💰 New balance: 200
```

### Scenario 2: Fix Accidental Bet

```
Admin: /setcoins 123456789 1000

Result:
✅ Set user 123456789 balance to 1000 coins
💰 Previous: 1200 → New: 1000
```

### Scenario 3: Penalize Rule Breaker

```
Admin: /removecoins 555666777 500

Result:
✅ Removed 500 coins from user 555666777
💰 New balance: 0
```

---

## Important Notes

### 1. Use User IDs, Not Usernames

**Recommended** ✅:
- Reply method: `/setcoins 500` (most reliable)
- Direct ID: `/setcoins 123456789 500`

**Not Recommended** ❌:
- Username: `/setcoins @john 500` (only if john's username is known in chat)

### 2. Get User ID

To find a user's ID:
1. **Method A**: Have them message bot with `/start`
   - Check logs or sent message
   - Their ID will be displayed

2. **Method B**: Reply to their message
   - Use reply method (most reliable)
   - Bot extracts ID automatically

3. **Method C**: Use @userinfobot
   - Message @userinfobot
   - It shows your user ID

### 3. Authorization

Only OWNER_ID can use admin commands:
```python
# In config.py
OWNER_ID = 123456789  # Your Telegram ID
```

If someone else tries:
```
❌ You are not authorized to use this command.
```

### 4. Data Persistence

All changes are auto-saved to `bot_data.json`:
```json
{
  "economy": {
    "123456789": 1500
  }
}
```

### 5. Tracking & Auditing

Every transaction is logged:
```python
"economy_log": [
  {
    "user_id": 123456789,
    "delta": 500,
    "new_balance": 1500,
    "reason": "Added by admin 987654321",
    "timestamp": "2024-01-15 10:30:45"
  }
]
```

---

## Troubleshooting

### Issue: "You are not authorized"

**Cause:** Your user ID is not OWNER_ID

**Fix:**
1. Get your Telegram ID
2. Update `config.py`:
   ```python
   OWNER_ID = YOUR_ID_HERE
   ```
3. Restart bot

### Issue: "Could not find user @username"

**Cause:** Username not in current chat's members

**Fix:**
1. Use reply method (most reliable)
2. Or use direct user ID
3. Have bot and user in same group first

### Issue: "User only has X coins"

**Cause:** Trying to remove more coins than user has

**Fix:**
1. Check user's balance: `/top`
2. Reduce removal amount
3. Or use `/setcoins` instead

### Issue: Command not working

**Cause:** Bot token or configuration issue

**Fix:**
1. Check bot is running: `python main.py`
2. Check bot token in `config.py`
3. Restart bot
4. Check `bot.log` for errors

---

## Command Summary Table

| Command | Reply Format | Direct ID Format | Effect |
|---------|-------------|------------------|--------|
| addcoins | `/addcoins 100` | `/addcoins 123 100` | Add coins |
| removecoins | `/removecoins 100` | `/removecoins 123 100` | Remove coins |
| setcoins | `/setcoins 100` | `/setcoins 123 100` | Set exact balance |

---

## Logging & Monitoring

View logs to see all admin actions:

**In console:**
```
✅ Resolved user from reply: 123456789
💰 Admin 987654321 added 500 coins to 123456789. New balance: 1500
```

**In bot.log file:**
```
[2024-01-15 10:30:45] INFO: ✅ Resolved user from reply: 123456789
[2024-01-15 10:30:46] INFO: 💰 Admin 987654321 added 500 coins to 123456789. New balance: 1500
```

**In bot_data.json:**
```json
{
  "economy_log": [
    {
      "user_id": 123456789,
      "delta": 500,
      "new_balance": 1500,
      "reason": "Added by admin 987654321",
      "timestamp": "2024-01-15 10:30:46"
    }
  ]
}
```

---

## Version History

- **v3.2** (Latest) - Fixed user tracking, added reply support, improved logging
- **v3.1** - Basic admin commands
- **v3.0** - Initial economy system

---

**Status**: ✅ Ready for Production
**Last Updated**: May 2026
