# 💰 WHISKY BOT - VIRTUAL ECONOMY SYSTEM

## 🎮 Overview

The economy system is a **FAKE/VIRTUAL GAMBLING SYSTEM** for entertainment purposes only. It uses virtual coins that have **NO real-world value**, no crypto, no withdrawals, and no actual monetary value.

⚠️ **IMPORTANT DISCLAIMER**: This is entertainment only. No real money is involved.

## 📊 System Components

### 1. **Economy Module** (`economy.py`)
Manages all coin-related operations:
- User balances
- Transactions (add/remove/set coins)
- Daily rewards
- Leaderboard
- Transaction logging

### 2. **Gambling Games** (`gambling.py`)
Implements entertainment games:
- **Coinflip**: 50/50 chance, 2x multiplier on win
- **Slots**: Slot machine with jackpot possibility
- **Dice**: Roll vs bot, 50% win rate
- **Scratch Card**: Hidden prize game (bonus)

### 3. **Admin Economy** (`admin_economy.py`)
Owner-only commands for managing coins:
- `/addcoins` - Add coins to users
- `/removecoins` - Remove coins from users
- `/setcoins` - Set exact balance

## 💎 Economy System Settings

All settings are configured in `config.py`:

```python
# Owner ID - only this user can use admin economy commands
OWNER_ID = 8577797097

# Starting balance for new users
STARTING_BALANCE = 100

# Daily reward amount
DAILY_REWARD = 50

# Betting limits
MIN_BET = 1
MAX_BET = 1000

# Cooldowns (seconds)
DAILY_COOLDOWN = 86400  # 24 hours
GAMBLING_COOLDOWN = 2   # seconds between gambles

# Game settings
COINFLIP_MULTIPLIER = 2        # Win = 2x bet
SLOTS_JACKPOT_MULTIPLIER = 10  # Jackpot = 10x bet
SLOTS_WIN_MULTIPLIER = 1.5     # Regular win = 1.5x bet
DICE_WIN_MULTIPLIER = 1.8      # Win = 1.8x bet
```

## 🎮 User Commands

### `/balance`
Shows your current coin balance and disclaimers.

```
Usage: /balance
Response: Shows coins, account info, and game suggestions
```

### `/daily`
Claim 50 free coins every 24 hours.

```
Usage: /daily
Response: ✅ Claimed 50 coins! (if eligible)
          ⏱️ Wait X hours (if already claimed)
```

### `/coinflip <amount>`
50/50 gamble - double your coins or lose them.

```
Usage: /coinflip 50
Result: 
  - Win (50%): Gain 100 coins (2x multiplier)
  - Lose (50%): Lose 50 coins
```

### `/slots <amount>`
Spin the slot machine with possible jackpot.

```
Usage: /slots 25
Result:
  - Jackpot (2%): Win 250 coins (10x multiplier)
  - Regular Win (30%): Win ~37 coins (1.5x multiplier)
  - Loss (68%): Lose 25 coins
```

### `/dicegame <amount>`
Roll dice vs bot. Higher roll wins.

```
Usage: /dicegame 30
Result:
  - Your roll > Bot roll: Win 54 coins (1.8x multiplier)
  - Your roll < Bot roll: Lose 30 coins
  - Tie: No coins gained or lost
```

### `/top`
View the leaderboard of richest users.

```
Usage: /top
Response: Shows top 10 users ranked by coin balance
```

## 🔑 Admin Economy Commands

**⚠️ RESTRICTED TO OWNER ONLY (User ID: 8577797097)**

### `/addcoins <user_id> <amount>`
Add coins to a user's balance.

```
Usage: /addcoins 12345 100
Effect: User gains 100 coins
Permission: OWNER_ID only
```

### `/removecoins <user_id> <amount>`
Remove coins from a user's balance.

```
Usage: /removecoins 12345 50
Effect: User loses 50 coins (if they have enough)
Permission: OWNER_ID only
```

### `/setcoins <user_id> <amount>`
Set exact balance for a user.

```
Usage: /setcoins 12345 500
Effect: User balance set to exactly 500 coins
Permission: OWNER_ID only
```

## 📊 Data Structure

Economy data is stored in `bot_data.json`:

```json
{
  "economy": {
    "12345": 500,
    "67890": 150,
    ...
  },
  "daily_claims": {
    "12345": "2024-01-15T10:30:00",
    ...
  },
  "economy_log": [
    {
      "timestamp": "2024-01-15T10:30:00",
      "type": "ACCOUNT_CREATED",
      "user_id": 12345,
      "amount": 0,
      "new_balance": 100,
      "reason": "New account"
    },
    ...
  ]
}
```

## 🛡️ Anti-Abuse Measures

1. **Bet Validation**
   - Minimum bet: 1 coin
   - Maximum bet: 1000 coins
   - Prevents negative bets

2. **Balance Checking**
   - Cannot bet more than owned coins
   - Prevents overspending

3. **Cooldowns**
   - Daily reward: Once per 24 hours
   - Gambling: 2 seconds between attempts

4. **Transaction Logging**
   - All transactions logged
   - Last 1000 transactions kept
   - Used for audit trail

## 🎯 Future Expansion Ideas

1. **More Games**
   - Roulette
   - Blackjack
   - Card games

2. **Seasonal Rewards**
   - Holiday bonuses
   - Milestone rewards

3. **Betting Systems**
   - Multiplayer betting
   - Tournament mode

4. **Item Shop**
   - Buy cosmetics with coins
   - Auction system

5. **Weekly Challenges**
   - Special tasks for bonus coins
   - Difficulty levels

## ⚠️ Important Notes

- **VIRTUAL ONLY**: No real money or crypto involved
- **FOR ENTERTAINMENT**: Not gambling in real sense
- **NO WITHDRAWALS**: Coins cannot be converted to money
- **MODULAR CODE**: Easy to expand and modify
- **SAFE FOR ALL AGES**: No real financial risk
- **OPTIONAL FEATURE**: Can be disabled in config

## 📝 Logging

All economy actions are logged:

```
[timestamp] - [level] - [module] - [message]
2024-01-15 10:30:00 - INFO - economy - 💰 [ADD_COINS] User 12345: 100 coins (Coinflip win: +100)
```

## 🚀 Getting Started

1. Users receive 100 coins when they first use `/balance`
2. Claim 50 free coins daily with `/daily`
3. Play games to win/lose coins with `/coinflip`, `/slots`, `/dicegame`
4. Check leaderboard with `/top`
5. Only OWNER_ID (8577797097) can manage admin coins

## 📞 Support

For issues or questions:
1. Check the logs in `bot.log`
2. Verify settings in `config.py`
3. Review economy transaction history
4. Contact bot admin

---

**Last Updated**: January 2024
**System Version**: 3.0
**Status**: ✅ Active
