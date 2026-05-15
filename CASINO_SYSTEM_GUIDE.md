# 🎰 CASINO ECONOMY SYSTEM - COMPLETE GUIDE

## ✨ What You Have

A complete **virtual casino/economy system** for your Telegram bot with:

✅ **Beautiful Animations** - Coin flips, dice rolls, spinning slots
✅ **Clean Code Structure** - Modular, easy to understand, well-commented
✅ **Virtual Currency** - Fake coins only (no real money, no withdrawals)
✅ **Game Variety** - Coinflip, Slots, Dice, Scratch Card games
✅ **Admin Controls** - Owner-only commands to manage player coins
✅ **Anti-Spam** - Cooldowns and rate limiting to prevent abuse
✅ **Leaderboard** - Top 10 richest players ranked by balance
✅ **Daily Rewards** - 50 coins per day with 24-hour cooldown
✅ **Data Persistence** - All data saved to bot_data.json

## 🎮 Player Commands

### `/balance`
Shows your current coin balance with a beautiful card format.

```
╔════════════════════════════╗
║   💰 **YOUR ACCOUNT** 💰   ║
╠════════════════════════════╣
║  👤 PlayerName          ║
║  🪙 Coins: **1000**     ║
╚════════════════════════════╝
```

### `/daily`
Claim 50 free coins once per day (24-hour cooldown).

```
╔════════════════════════════╗
║     🎁 **DAILY REWARD** 🎁 ║
╠════════════════════════════╣
║  ✅ Claimed **50** coins!  ║
║  Come back tomorrow for more!║
╚════════════════════════════╝
```

### `/coinflip <amount>`
Flip a coin for 50/50 odds. Win 2x your bet or lose it.

```
🪙 Flipping coin...
🪙 Flipping coin .
🪙 Flipping coin ..
🪙 Flipping coin ...

━━━━━━━━━━━━━━━━━
🎉 **COINFLIP RESULT** 🎉
━━━━━━━━━━━━━━━━━

🪙 **HEADS!** You won 200 coins!

━━━━━━━━━━━━━━━━━
💰 Balance: **1000** → **1200**
━━━━━━━━━━━━━━━━━
```

**How it works:**
- `/coinflip 100` - Bet 100 coins
- 50% chance to win: earn 200 coins
- 50% chance to lose: lose 100 coins

### `/slots <amount>`
Spin the slot machine! Win up to 10x your bet.

```
🎰 Spinning...
🎰 [🍎] [🍊] [🍋]
🎰 [🍊] [🍋] [🍌]
🎰 [🍋] [🍌] [🍉]
🎰 [🍌] [🍉] [💎]

━━━━━━━━━━━━━━━━━
🎉 **SLOTS RESULT** 🎉
━━━━━━━━━━━━━━━━━

🎰 [💎] [💎] [💎] JACKPOT! You won 1000 coins!

━━━━━━━━━━━━━━━━━
💰 Balance: **100** → **1100**
━━━━━━━━━━━━━━━━━
```

**Odds:**
- 2% chance to win 10x (JACKPOT!)
- 30% chance to win 1.5x (regular win)
- 68% chance to lose bet

### `/dicegame <amount>`
Roll dice vs the bot! Win if you roll higher (1-6).

```
🎲 Rolling...
🎲 Rolling... 1
🎲 Rolling... 2
🎲 Rolling... 3
🎲 Rolling... 4
🎲 Rolling... 5
🎲 Rolling... 6

━━━━━━━━━━━━━━━━━
🎉 **DICE RESULT** 🎉
━━━━━━━━━━━━━━━━━

🎲 You rolled 5, Bot rolled 3 - You won 180 coins!

━━━━━━━━━━━━━━━━━
💰 Balance: **1000** → **1180**
━━━━━━━━━━━━━━━━━
```

**How it works:**
- Roll higher than bot to win 1.8x your bet
- Tie = no gain or loss
- Roll lower = lose your bet

### `/top`
View the leaderboard of richest players.

```
╔════════════════════════════╗
║  🏆 **RICHEST USERS** 🏆  ║
╠════════════════════════════╣
║ 🥇 #12345      5000 coins ║
║ 🥈 #67890      3500 coins ║
║ 🥉 #11111      2000 coins ║
║ 4️⃣  #22222      1500 coins ║
║ 5️⃣  #33333      1000 coins ║
╚════════════════════════════╝
```

## 🛡️ Admin Commands (Owner Only)

Replace `OWNER_ID` in config.py with your Telegram user ID to use these commands.

### `/addcoins <user_id> <amount>`
Add coins to a player's account.

```
/addcoins 12345 500
✅ Added 500 coins to user #12345
New balance: 1500 coins
```

### `/removecoins <user_id> <amount>`
Remove coins from a player's account.

```
/removecoins 12345 200
✅ Removed 200 coins from user #12345
New balance: 1300 coins
```

### `/setcoins <user_id> <amount>`
Set a player's balance to exact amount.

```
/setcoins 12345 1000
✅ Set user #12345 balance to 1000 coins
```

## 📁 Code Structure

### `economy.py` (Balance Management)
Core system for handling player money.

**Main functions:**
- `get_balance(user_id)` - Get player's coins
- `add_coins(user_id, amount, reason)` - Add coins
- `remove_coins(user_id, amount, reason)` - Remove coins
- `set_coins(user_id, amount, reason)` - Set exact balance
- `validate_bet(amount, user_balance)` - Check if bet is valid
- `claim_daily(user_id)` - Claim daily reward
- `get_top_users(limit)` - Get leaderboard

### `gambling.py` (Game Logic)
All game implementations.

**Games:**
- `coinflip(bet_amount)` - 50/50 coin flip
- `slots(bet_amount)` - 3-reel slot machine
- `dice(bet_amount)` - Dice vs bot
- `scratch_card(bet_amount)` - Hidden prizes (bonus)

### `ui_animations.py` (Visual Effects)
Beautiful animations and formatting.

**Animation functions:**
- `animate_coin_flip()` - Coin flip animation
- `animate_slots()` - Slots spinning
- `animate_dice_roll()` - Dice rolling

**Format functions:**
- `format_result(game, data)` - Game result card
- `format_balance_card(balance)` - Account display
- `format_daily_reward(coins)` - Daily card
- `format_leaderboard(users)` - Top 10 display

### `admin_economy.py` (Admin Commands)
Owner-only coin management.

**Functions:**
- `addcoins(update, context, economy)` - Add coins
- `removecoins(update, context, economy)` - Remove coins
- `setcoins(update, context, economy)` - Set balance
- `owner_only` - Authorization decorator

### `config.py` (Settings)
All configuration in one place.

**Economy settings:**
```python
OWNER_ID = 8577797097              # Your Telegram ID
STARTING_BALANCE = 100             # Coins for new players
DAILY_REWARD = 50                  # Free coins per day
MIN_BET = 1                        # Minimum bet amount
MAX_BET = 1000                     # Maximum bet amount
DAILY_COOLDOWN = 86400             # 24 hours in seconds
GAMBLING_COOLDOWN = 2              # Seconds between bets
ENABLE_ECONOMY = True              # Feature toggle
```

**Game odds:**
```python
COINFLIP_ODDS = 50                 # 50% win chance
COINFLIP_MULTIPLIER = 2            # 2x winnings
SLOTS_JACKPOT_CHANCE = 0.02        # 2% chance for 10x
SLOTS_WIN_CHANCE = 0.30            # 30% chance for 1.5x
DICE_WIN_CHANCE = 0.50             # 50% win chance
DICE_WIN_MULTIPLIER = 1.8          # 1.8x winnings
SCRATCH_CARD_ODDS = {              # Tiered odds
    'jackpot': 0.05,
    'big_win': 0.15,
    'win': 0.25,
    'loss': 0.55
}
```

### `main.py` (Bot Core)
Central command handler that brings everything together.

**What it does:**
1. Loads economy system
2. Registers all game commands
3. Integrates animations
4. Handles messages and updates
5. Saves data after each transaction

## 🔧 Setup Instructions

### 1. Install Required Packages
```bash
pip install python-telegram-bot
```

### 2. Update Your User ID
Edit `config.py` and replace with your actual Telegram ID:

```python
OWNER_ID = YOUR_ID_HERE  # Get from @userinfobot
```

### 3. Check Configuration
```python
# In config.py, verify:
ENABLE_ECONOMY = True     # Should be True
STARTING_BALANCE = 100    # New player starting coins
DAILY_REWARD = 50         # Free coins per day
MIN_BET = 1               # Minimum bet
MAX_BET = 1000            # Maximum bet
```

### 4. Start the Bot
```bash
python main.py
```

## 📊 Data Storage

All data is saved to `bot_data.json`:

```json
{
  "economy": {
    "12345": 1500,      // User ID → Balance
    "67890": 2000
  },
  "daily_claims": {
    "12345": 1705276800  // User ID → Timestamp
  },
  "economy_log": [
    {
      "user_id": 12345,
      "delta": 500,
      "new_balance": 1500,
      "reason": "Coinflip win",
      "timestamp": "2024-01-15 10:30:45"
    }
  ]
}
```

**Auto-save:** Data saves automatically after each transaction.

## 🚀 Quick Start

1. **New player gets:** 100 coins
2. **First action:** `/balance` to see coins
3. **Earn daily:** `/daily` for 50 free coins
4. **Play games:**
   - `/coinflip 10` - Bet 10 coins
   - `/slots 10` - Spin slots
   - `/dicegame 10` - Roll dice
5. **Check rank:** `/top` to see leaderboard

## ⚠️ Safety Features

### Virtual Only
- No real money involved
- No withdrawals possible
- No payments accepted
- Entertainment only

### Anti-Abuse
- 24-hour cooldown on daily rewards
- 2-second cooldown between bets
- Bet limits (min/max)
- Balance validation before every bet
- Spam prevention

### Error Handling
- Clear error messages
- Graceful fallback if something breaks
- Transaction logging for debugging
- Automatic data backup in JSON

## 🎨 Visual Features

### Animations
- Coinflip: 4-step spinning animation
- Slots: 4-frame spinning reels
- Dice: Rolling numbers 1-6

### Formatting
- Beautiful box borders (╔═╗╠╣║)
- Emoji-based icons (💰🪙🎲🎰)
- Clear separators (━━━━━━━)
- Structured layouts
- Win/loss styling

### Performance
- 0.1-0.4s animation delays
- Smooth message editing
- No blocking operations
- Fast response times

## 🐛 Troubleshooting

### "Invalid command" error
**Problem:** Bot doesn't recognize commands
**Solution:** 
1. Restart bot: `Ctrl+C` then `python main.py`
2. Check ENABLE_ECONOMY=True in config.py
3. Verify imports in main.py

### "You don't have enough coins"
**Problem:** Bet is too high
**Solution:**
1. Check balance: `/balance`
2. Reduce bet amount
3. Claim daily reward: `/daily`

### Bot not responding to games
**Problem:** Commands not working
**Solution:**
1. Check bot has MESSAGE and EDIT permissions
2. Verify asyncio is installed
3. Check logs for errors

### Data not saving
**Problem:** Progress lost after restart
**Solution:**
1. Check bot_data.json exists
2. Verify write permissions in folder
3. Check bot.log for save errors

## 🔄 How It Works

### User Flow
```
User sends /coinflip 100
  ↓
Bot checks: Has 100 coins? YES
  ↓
Bot shows animation (🪙 Flipping coin...)
  ↓
Bot plays game (50/50 chance)
  ↓
Bot removes bet from balance (100 coins)
  ↓
Bot determines: Win or Loss?
  ↓
If WIN: Add 200 coins
If LOSS: Keep removed (already subtracted)
  ↓
Bot shows beautiful result card
  ↓
Bot saves to bot_data.json
```

### Animation Flow
```
1. Send: "🪙 Flipping coin..."
2. Wait: 0.3 seconds
3. Edit: "🪙 Flipping coin ."
4. Wait: 0.2 seconds
5. Edit: "🪙 Flipping coin .."
6. Wait: 0.2 seconds
7. Edit: "🪙 Flipping coin ..."
8. Wait: 0.4 seconds (suspense)
9. Delete animation message
10. Show result card
```

## 💡 Tips

### For Players
- Start with small bets to learn odds
- Use `/daily` every day for free coins
- Slots have best jackpot chance (10x)
- Dice is most balanced game
- Check `/top` to see competition

### For Developers
- Modify odds in config.py
- Add new games in gambling.py
- Change animations in ui_animations.py
- Add commands in main.py
- Debug with bot.log

### For Admins
- Use `/addcoins` to reward active players
- Use `/removecoins` to reverse bad bets
- Use `/setcoins` to reset accounts
- Monitor bot.log for issues
- Back up bot_data.json regularly

## 📈 Future Ideas

1. **Win Streaks** - Track consecutive wins
2. **Achievements** - Badges for milestones
3. **Seasonal Leaderboards** - Weekly/monthly ranks
4. **More Games** - Roulette, BlackJack, Poker
5. **Trading** - Players trade coins
6. **Betting Multipliers** - Increase odds with risk
7. **Sound Effects** - Audio on wins
8. **Achievements** - Badges and titles
9. **Team Battles** - Guild/squad system
10. **Seasonal Events** - Special limited games

## 📞 Support

**For Issues:**
1. Check bot.log for error messages
2. Verify config.py settings
3. Restart bot: `python main.py`
4. Check Python version: `python --version`
5. Reinstall packages: `pip install -r requirements.txt`

**Common Checks:**
```bash
# Verify files exist
ls *.py | grep economy

# Check syntax
python -m py_compile *.py

# Test with debug mode
DEBUG=1 python main.py
```

---

**Version**: 3.1 (Final)
**Status**: ✅ Ready to Deploy
**Last Updated**: May 2026
**Support**: Check bot.log and config.py
