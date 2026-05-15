# 🎮 ECONOMY SYSTEM - QUICK START GUIDE

## ✅ What's New

Your bot now has a complete **VIRTUAL GAMBLING/CASINO SYSTEM** with:

- 💰 Virtual coin economy (100 coins starter)
- 🎮 3 gambling games (coinflip, slots, dice)
- 🏆 Leaderboard system
- 🎁 Daily free coins
- 👑 Owner-only admin commands
- 📊 Transaction logging
- ⚠️ Anti-abuse protections

## 🚀 How to Test

### Step 1: Start the Bot
Run your bot as normal:
```bash
python main.py
```

### Step 2: Test User Commands

**Check Balance:**
```
/balance
```
→ Shows 100 coins (new user starter balance)

**Claim Daily Reward:**
```
/daily
```
→ Gains 50 coins (wait 24h for next claim)

**Play Coinflip (50/50):**
```
/coinflip 10
```
→ Win: +20 coins, Lose: -10 coins

**Play Slots:**
```
/slots 25
```
→ Jackpot (2%): +250 coins
→ Win (30%): +~37 coins
→ Loss (68%): -25 coins

**Play Dice Game:**
```
/dicegame 30
```
→ Win: +54 coins, Lose: -30 coins, Tie: +0 coins

**View Leaderboard:**
```
/top
```
→ Shows top 10 richest users

### Step 3: Test Admin Commands (OWNER ONLY)

**Only user ID 8577797097 can use:**

```
/addcoins 12345 100
→ Adds 100 coins to user 12345

/removecoins 12345 50
→ Removes 50 coins from user 12345

/setcoins 12345 500
→ Sets user 12345 balance to exactly 500 coins
```

**Other users get:** ❌ "You are not authorized to use this command."

## 📁 Files Created/Modified

### New Files Created:
- ✅ `economy.py` - Core economy system
- ✅ `gambling.py` - Game logic
- ✅ `admin_economy.py` - Admin commands
- ✅ `ECONOMY_SYSTEM.md` - Full documentation

### Files Modified:
- ✅ `config.py` - Added economy settings & OWNER_ID
- ✅ `main.py` - Integrated all commands & handlers

## 📊 Data Storage

All data automatically saved in `bot_data.json`:
```json
{
  "economy": {
    "user_id": coins_balance,
    ...
  },
  "daily_claims": {
    "user_id": "last_claim_timestamp",
    ...
  },
  "economy_log": [
    transaction records...
  ]
}
```

## ⚙️ Configuration

Edit `config.py` to customize:

```python
OWNER_ID = 8577797097              # Change admin ID
STARTING_BALANCE = 100             # Starting coins for new users
DAILY_REWARD = 50                  # Coins per daily claim
MIN_BET = 1                        # Minimum bet allowed
MAX_BET = 1000                     # Maximum bet allowed
COINFLIP_MULTIPLIER = 2            # Win multiplier (2x = double)
SLOTS_JACKPOT_MULTIPLIER = 10      # Jackpot reward (10x)
SLOTS_WIN_MULTIPLIER = 1.5         # Regular win (1.5x)
DICE_WIN_MULTIPLIER = 1.8          # Dice win (1.8x)
```

## 🔒 Security Features

✅ Only OWNER_ID can use admin commands
✅ Automatic bet validation (min/max)
✅ Prevents negative balances
✅ Cooldowns (daily, gambling)
✅ Transaction audit logs
✅ Input validation
✅ Clear error messages

## 📋 Command Reference

### User Commands:
| Command | Usage | Effect |
|---------|-------|--------|
| `/balance` | /balance | Show current coins |
| `/daily` | /daily | Claim 50 coins (24h cooldown) |
| `/coinflip` | /coinflip 10 | 50/50 double or lose |
| `/slots` | /slots 25 | Spin slots machine |
| `/dicegame` | /dicegame 30 | Roll vs bot |
| `/top` | /top | Leaderboard (top 10) |

### Admin Commands (OWNER_ID = 8577797097 ONLY):
| Command | Usage | Effect |
|---------|-------|--------|
| `/addcoins` | /addcoins 12345 100 | Add 100 coins to user |
| `/removecoins` | /removecoins 12345 50 | Remove 50 coins |
| `/setcoins` | /setcoins 12345 500 | Set balance to 500 |

## 📝 Important Notes

⚠️ **VIRTUAL CURRENCY ONLY**
- No real money involved
- No crypto
- No withdrawals
- For entertainment only
- Safe for all ages

✅ **Modular Design**
- Easy to expand
- Add new games easily
- Configurable odds
- Scalable system

✅ **Logging & Auditing**
- All transactions logged
- Complete audit trail
- Debug info available
- Activity tracking

## 🐛 Troubleshooting

### Issue: "You are not authorized to use this command"
**Solution:** Admin commands only work for user ID 8577797097

### Issue: "❌ Minimum bet is 1 coins"
**Solution:** Bet amount must be >= 1 and <= 1000

### Issue: "❌ You only have X coins"
**Solution:** Can't bet more than owned coins

### Issue: Daily reward shows cooldown
**Solution:** Wait 24 hours from last claim

## 🚀 Next Steps

1. ✅ Test all commands with test users
2. ✅ Check leaderboard after some games
3. ✅ Test admin commands (admin user only)
4. ✅ Review logs in `bot.log`
5. ✅ Verify data in `bot_data.json`
6. ✅ Adjust game odds in `config.py` if needed

## 📚 Full Documentation

See `ECONOMY_SYSTEM.md` for:
- Complete system overview
- Detailed command descriptions
- Game mechanics and odds
- Data structure
- Future expansion ideas

## 💡 Tips

- Users start with 100 coins
- Encourage `/daily` for free coins
- Leaderboard motivates competition
- Adjust multipliers for difficulty
- Log file helps debug issues

---

**Status**: ✅ Ready to Use
**Version**: 3.0
**Tested**: All core features functional
**Support**: Check logs for errors
