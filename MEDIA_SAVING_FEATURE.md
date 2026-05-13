# 📸 Media Saving Feature - Complete Guide

## Overview
The bot now automatically saves **all pictures and messages** sent in the group to disk storage. This feature is enabled by default and runs transparently without disrupting normal bot operations.

---

## 🎯 What Gets Saved?

### Photos/Images
- **Format:** JPG files (highest resolution available)
- **Storage:** `saved_media/<user_id>/` folder
- **Naming:** `YYYYMMDD_HHMMSS_username.jpg`
- **Metadata:** Logged with user ID and timestamp

### Messages
- **Storage:** `saved_messages.json` file
- **Types:** Text, captions, videos, audio, documents
- **Metadata:** User ID, username, timestamp, message type, content (first 500 chars)
- **Limit:** Last 10,000 messages stored (to prevent file bloat)

### Other Media
- Videos (logged as metadata)
- Audio files (logged as metadata)
- Documents (logged as metadata)

---

## 📁 Storage Structure

```
project_root/
├── saved_media/                    # Photo storage directory
│   ├── 12345678/                   # User ID folder
│   │   ├── 20260513_143025_user1.jpg
│   │   ├── 20260513_143045_user1.jpg
│   │   └── ...
│   ├── 87654321/                   # Another user
│   │   ├── 20260513_144030_user2.jpg
│   │   └── ...
│   └── ...
│
├── saved_messages.json             # All messages log
├── bot_data.json                   # Bot statistics
├── bot.log                         # Bot activity log
└── ...
```

---

## ⚙️ Configuration

The feature is configured in `config.py`:

```python
# Media Storage Settings
MEDIA_STORAGE_DIR = "saved_media"      # Directory for photos
MESSAGES_LOG_FILE = "saved_messages.json"  # Message log file
ENABLE_MEDIA_SAVE = True               # Master enable/disable switch
```

### To Disable Media Saving
Edit `config.py` and set:
```python
ENABLE_MEDIA_SAVE = False
```

---

## 📊 View Saved Media Statistics

Use the admin-only command:

```
/media_stats
```

**Output includes:**
- Total number of photos saved
- Photos per user (top 10)
- Total messages saved
- Message breakdown by type (text, photo, video, etc.)
- Storage location information

**Example Output:**
```
📊 MEDIA & MESSAGE STORAGE STATS

📷 Total Photos: 156
Users with photos:
  • User 12345678: 45 photos
  • User 87654321: 32 photos
  • User 11111111: 22 photos

💬 Total Messages: 2,847
Message types:
  • text: 2,341
  • photo: 156
  • caption: 245
  • video: 85
  • document: 20

📁 Storage directory: `saved_media`
📄 Messages log: `saved_messages.json`
```

---

## 🔄 How It Works

### Message Flow
1. **User sends message/photo to group**
2. **Bot receives update**
3. **PRIORITY 0: Media Saving** (NEW - happens FIRST)
   - Photos are downloaded and saved
   - Messages are logged to JSON
   - Other media types are recorded
4. **PRIORITY 1-3: Normal processing** (continues as usual)
   - Ghost mode checking
   - Speak mode responses
   - NSFW filtering
   - AI commands

### Key Features
- ✅ **Asynchronous**: Doesn't block other bot operations
- ✅ **Automatic**: No admin action needed
- ✅ **Transparent**: Users don't know/can't see it happening
- ✅ **Efficient**: Photos optimized (highest resolution, JPG format)
- ✅ **Safe**: Organized by user ID, timestamped

---

## 📝 Message Log Structure

`saved_messages.json` contains:
```json
{
  "messages": [
    {
      "timestamp": "2026-05-13T14:30:25.123456",
      "user_id": "12345678",
      "username": "John",
      "type": "text",
      "content": "Hello everyone!"
    },
    {
      "timestamp": "2026-05-13T14:30:45.654321",
      "user_id": "87654321",
      "username": "Alice",
      "type": "photo",
      "content": "Photo saved: 20260513_143045_alice.jpg"
    }
  ]
}
```

---

## 🛡️ Security & Privacy

- **Local Storage Only**: All files stored locally, not uploaded anywhere
- **User-Based Organization**: Photos grouped by user ID
- **No Content Modification**: Messages/photos saved as-is
- **Admin Only Stats**: Only admins can view media statistics
- **Automatic Cleanup**: Keeps only last 10,000 messages

---

## ⚡ Performance Impact

- **Minimal CPU**: Runs in background without blocking
- **Async Download**: Photos downloaded asynchronously
- **Efficient Storage**: JPG compression, message log limits
- **No Response Delay**: Doesn't slow down bot responses

---

## 🚀 Common Use Cases

1. **Group Moderation**: Review what was posted
2. **Record Keeping**: Keep archive of group activity
3. **Evidence**: Store proof of violations
4. **Analytics**: See who posts what type of content
5. **Recovery**: Retrieve accidentally deleted messages

---

## 🔧 Troubleshooting

### Photos Not Saving?
- Check if `ENABLE_MEDIA_SAVE = True` in config.py
- Ensure `saved_media/` directory exists (auto-created)
- Check bot permissions in Telegram
- Check disk space available

### Messages Log Getting Too Large?
- File auto-truncates at 10,000 messages
- Delete `saved_messages.json` to start fresh
- Configure smaller limit if needed

### Permission Errors?
- Ensure bot has file write permissions
- Check folder ownership and permissions
- Run bot with appropriate user privileges

---

## 📋 Implementation Details

### New Functions Added:

**`initialize_media_storage()`**
- Creates media directory on startup
- Ensures directory exists

**`save_photo(update, context)`**
- Downloads highest resolution photo
- Saves to user-specific folder
- Logs metadata

**`save_message_log(user_id, username, message_text, type)`**
- Appends message to JSON log
- Includes timestamp and metadata
- Auto-truncates to prevent bloat

**`media_stats(update, context)`** [Admin Command]
- Shows saved media statistics
- Displays photos per user
- Shows message type breakdown

### Modified Functions:

**`handle_message(update, context)`**
- Now saves all media FIRST (PRIORITY 0)
- Processes after saving completes
- Handles photos even without text

---

## 📚 Related Features

- **`/media_stats`** - View saved media statistics (admin)
- **`saved_media/`** - Photo storage directory
- **`saved_messages.json`** - Message log file
- **Config**: `MEDIA_STORAGE_DIR`, `MESSAGES_LOG_FILE`, `ENABLE_MEDIA_SAVE`

---

## 🎓 Example Usage

### For Admins:
```
/media_stats        # Check what's been saved
```

### Automatic:
- All messages automatically saved
- All photos automatically downloaded
- No commands needed

---

## ✅ Verification

To verify the feature is working:

1. Send a message in the group → Check `saved_messages.json`
2. Send a photo → Check `saved_media/<your_id>/`
3. Run `/media_stats` → Should show counts
4. Check logs → Should see "💬 Message saved" and "📷 Photo saved"

---

## 📞 Support

If you encounter issues:
1. Check bot logs: `bot.log`
2. Run `/media_stats` to see current state
3. Verify config settings in `config.py`
4. Ensure disk space available
5. Check file permissions

---

## 🎉 Summary

The bot now silently saves every message and photo sent in the group. Use `/media_stats` to monitor storage, and review `saved_messages.json` and `saved_media/` folder for your records!

**Feature Status:** ✅ **ACTIVE**
