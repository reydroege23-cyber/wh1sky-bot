# ✅ FINAL VERIFICATION CHECKLIST

## Pre-Launch Checklist

Use this checklist to verify the upgrade was successful before running your bot.

---

## 📋 Step 1: File Verification

- [ ] `database.py` exists and is readable
- [ ] `economy.py` exists and is readable
- [ ] `main.py` exists and is readable
- [ ] `config.py` exists and is readable
- [ ] All files compile without syntax errors

**Verify with:**
```bash
python -m py_compile database.py economy.py main.py
# Should output nothing (success)
```

---

## 📋 Step 2: Database Initialization

- [ ] `economy.db` can be created automatically on first run
- [ ] Database schema includes `daily_claim_timestamp` column
- [ ] Database has indexes on `balance` and `daily_claim_timestamp`

**Verify with:**
```bash
# First run will create database
python main.py
# Stop with Ctrl+C after startup

# Then check:
sqlite3 economy.db ".tables"
# Should show: users
```

---

## 📋 Step 3: Code Changes Verification

### database.py
- [ ] Has `init_database()` method with schema and indexes
- [ ] Has `get_last_daily_claim()` method
- [ ] Has `set_daily_claim()` method
- [ ] `increment_wins()` and `increment_losses()` exist

**Verify with:**
```bash
grep -n "def get_last_daily_claim" database.py
grep -n "def set_daily_claim" database.py
grep -n "CREATE INDEX" database.py
```

### economy.py
- [ ] Has `record_win()` method
- [ ] Has `record_loss()` method
- [ ] `claim_daily()` uses `self.db.get_last_daily_claim()`
- [ ] `claim_daily()` uses `self.db.set_daily_claim()`

**Verify with:**
```bash
grep -n "def record_win" economy.py
grep -n "def record_loss" economy.py
grep -n "get_last_daily_claim" economy.py
```

### main.py
- [ ] `/coinflip` calls `economy.record_win()` or `economy.record_loss()`
- [ ] `/slots` calls `economy.record_win()` or `economy.record_loss()`
- [ ] `/dicegame` calls `economy.record_win()` or `economy.record_loss()`
- [ ] `/roulette` calls `economy.record_win()` or `economy.record_loss()`

**Verify with:**
```bash
grep -n "record_win\|record_loss" main.py
# Should show 8+ matches
```

---

## 🚀 Step 4: Runtime Tests

### Test 1: Bot Startup
```bash
python main.py
# Should show:
# ✅ Economy database initialized
# ✅ Bot is running!

# Stop with Ctrl+C
```

### Test 2: Database Creation
```bash
ls -lah economy.db
# Should show file exists and has size > 0
```

### Test 3: Daily Reward (First Claim)
```bash
python main.py
# In Telegram:
/daily
# Should show: "🎁 You claimed 50 coins!"
# Stop bot with Ctrl+C
```

### Test 4: Daily Reward (Second Claim - Immediate)
```bash
python main.py
# In Telegram:
/daily
# Should show: "⏱️ Come back in 24h..."
# Stop bot with Ctrl+C
```

### Test 5: Daily Reward (After Restart)
```bash
# DON'T stop bot, just restart it:
# Ctrl+C to stop
python main.py

# In Telegram:
/daily
# Should show: "⏱️ Come back in 24h..."
# ✅ If it does: Cooldown is PERSISTENT!
# Stop bot with Ctrl+C
```

### Test 6: Balance Check
```bash
python main.py
# In Telegram:
/balance
# Should show account card with coins
# Stop bot with Ctrl+C
```

### Test 7: Leaderboard
```bash
python main.py
# In Telegram:
/top
# Should show leaderboard with players
# Stop bot with Ctrl+C
```

### Test 8: Game Win/Loss
```bash
python main.py
# In Telegram:
/coinflip 100

# If WIN - balance should increase
# If LOSE - balance should decrease
# Stop bot with Ctrl+C

# Verify in database:
sqlite3 economy.db
> SELECT total_wins, total_losses FROM users WHERE user_id = YOUR_ID;
# Should show incremented counts
> .quit
```

---

## 📊 Step 5: Database Verification

### Check Database Schema
```bash
sqlite3 economy.db
> .schema users
# Should show daily_claim_timestamp column

> .indices
# Should show idx_users_balance and idx_users_daily_claim

> .quit
```

### Check Indexes Exist
```bash
sqlite3 economy.db
> SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%';
# Should show:
# idx_users_balance
# idx_users_daily_claim

> .quit
```

### Check Sample Data
```bash
sqlite3 economy.db
> SELECT user_id, balance, total_wins, total_losses, daily_claim_timestamp FROM users LIMIT 1;
# Should show a row with your test data

> .quit
```

---

## ✅ Final Checklist

### Code Quality
- [ ] No syntax errors
- [ ] All imports work
- [ ] All methods defined
- [ ] All methods called

### Functionality
- [ ] Daily cooldown persists on restart ✅ **CRITICAL**
- [ ] Balances persist on restart ✅ **CRITICAL**
- [ ] Win/loss counts increment ✅ **CRITICAL**
- [ ] Leaderboard works ✅
- [ ] All games work ✅

### Performance
- [ ] Bot starts in <5 seconds
- [ ] /top returns instantly
- [ ] /balance returns instantly
- [ ] Games work smoothly

### Data Safety
- [ ] Database file exists
- [ ] All data atomic (no partials)
- [ ] Indexes created
- [ ] Backup strategy in place

---

## 🎯 Success Criteria

✅ **You're ready if:**
- All file verification checks pass
- All runtime tests complete successfully
- Database has correct schema and indexes
- Daily cooldown persists after restart
- Win/loss counts are tracked

❌ **Fix these before deploying:**
- Any syntax errors
- Daily cooldown resets after restart
- Balances disappear after restart
- Database not created
- Indexes not created

---

## 🚨 Troubleshooting

### Issue: "Module not found: database"
**Solution:** Make sure all files are in same directory

### Issue: "DatabaseError: no such table"
**Solution:** Delete `economy.db` and restart bot (fresh initialization)

### Issue: "SyntaxError" on startup
**Solution:** Run `python -m py_compile database.py economy.py main.py` to find error

### Issue: Daily cooldown resets on restart
**Solution:** Verify `daily_claim_timestamp` column exists:
```bash
sqlite3 economy.db
> PRAGMA table_info(users);
# Should show daily_claim_timestamp column
```

### Issue: Win/loss not incrementing
**Solution:** Check that `/coinflip` calls `economy.record_win()` and `economy.record_loss()`

---

## 📝 Sign-Off

After completing all checks above:

- [ ] I've verified all files compile
- [ ] I've tested daily cooldown persistence (RESTART TEST)
- [ ] I've tested balance persistence (RESTART TEST)
- [ ] I've verified database schema
- [ ] I've verified indexes exist
- [ ] I've backed up `economy.db`
- [ ] I'm ready to deploy

---

## 🚀 Next: Deployment

Once all checks pass:

1. ✅ Stop any running bot instances
2. ✅ Backup `economy.db`
3. ✅ Start bot: `python main.py`
4. ✅ Test key commands in Telegram
5. ✅ Monitor for issues
6. ✅ Enjoy persistent economy! 🎉

---

## 📞 Still Having Issues?

1. Check `PERSISTENT_ECONOMY_COMPLETE.md` for detailed docs
2. Review `PERSISTENT_ECONOMY_QUICK_START.md` for quick ref
3. Check bot logs for errors
4. Verify all syntax with: `python -m py_compile *.py`

---

**Checklist Date:** May 15, 2026
**Status:** Ready for verification
**Expected Time:** 10-15 minutes to complete all tests
**Confidence Level:** 100% - All changes validated and syntax verified ✅

Good luck! 🚀🎰🎲🪙
