# Elena Grammar Bot 🤖📚

Telegram bot that generates Russian grammar practice sentences using DeepSeek AI and distributes them to multiple student chats.

## Features ✨

- 🎯 Generate 6 diverse Russian sentences for 15 different grammar structures
- 📤 Send selected sentences to multiple student chats simultaneously
- 🔔 Automatic Hebrew reminders at 10:00 and 16:00 UTC
- 🎲 AI-powered sentence variety (no more repetitive examples!)
- ⚡ Easy to add/remove students without code changes
- 🔄 Auto-restart via systemd

---

## Quick Start 🚀

### 1. Add New Student Chat ID

**Easiest Method** - Edit `.env` file:
```bash
nano .env
# Update this line:
TARGET_CHAT_IDS=123456789,-987654321,444555666
#                                    ^ add new ID here
sudo systemctl restart elena-grammar-bot.service
```

**Alternative** - Edit Python code:
```python
TARGET_CHATS = [
    (123456789, "Elena"),
    (-987654321, "Maria"),
    (444555666, "Dmitry"),  # <-- Add new student here
]
```

### 2. Get Chat ID
1. Add bot to the chat
2. Send any message
3. Visit: `https://api.telegram.org/bot<BOT_TOKEN>/getUpdates`
4. Find: `"chat":{"id":123456789}`

### 3. Usage
- `/start` - Initialize bot
- `/quiz` - Generate 6 practice sentences
- Click buttons to send sentences to all configured chats
- Sentences expire after 30 seconds

---

## Configuration Methods 🔧

### Method 1: Environment Variable (Recommended)
```bash
# .env file
TARGET_CHAT_IDS=123456789,-987654321,111222333
```
✅ No code changes needed  
✅ Easy to update  
✅ Keeps secrets separate

### Method 2: Code List
```python
# elena_grammar_bot.py
TARGET_CHATS = [
    (123456789, "Elena"),
    (-987654321, "Maria"),
]
```
✅ See student names  
✅ Better documentation  
❌ Requires code edit

**Choose one method!** If both are set, .env takes priority.

---

## File Structure 📁

```
~/bots/elena-grammar-bot/
├── elena_grammar_bot.py    # Main bot code
├── .env                     # Your config (create from env_example)
├── env_example              # Template
├── venv/                    # Python virtual environment
├── DEPLOYMENT_GUIDE.md      # Full deployment instructions
└── README.md               # This file
```

---

## Grammar Structures 📖

The bot practices these 15 structures:
- Comparatives: "Not nearly as... as", "Not quite as... as"
- Passives: Simple past, Simple future, Present continuous
- Conditionals: Second, Third, Mixed
- Modals: "Should have", "Must have", "Could never get used to"
- Wishes: Present regret, Past regret
- Patterns: "The more... the more", "Worth + -ing"

---

## Service Management 🔄

```bash
# Start/Stop/Restart
sudo systemctl start elena-grammar-bot.service
sudo systemctl stop elena-grammar-bot.service
sudo systemctl restart elena-grammar-bot.service

# View logs
sudo journalctl -u elena-grammar-bot.service -f

# Check status
sudo systemctl status elena-grammar-bot.service
```

---

## Troubleshooting 🔍

### Bot not responding?
```bash
# Check if running
sudo systemctl status elena-grammar-bot.service

# View recent errors
sudo journalctl -u elena-grammar-bot.service -n 50

# Restart
sudo systemctl restart elena-grammar-bot.service
```

### Sentences too repetitive?
- The bot tracks recent topics automatically
- Increased temperature (0.9) for more variety
- Each grammar structure gets unique contexts

### Student not receiving messages?
1. Verify chat ID is correct
2. Check bot is admin (for groups)
3. Student may have blocked bot
4. View logs: `sudo journalctl -u elena-grammar-bot.service -f`

---

## API Keys Required 🔑

1. **Telegram Bot Token** - Get from [@BotFather](https://t.me/BotFather)
2. **DeepSeek API Key** - Get from [platform.deepseek.com](https://platform.deepseek.com)

---

## Environment Variables Reference 📝

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ Yes | Your Telegram bot token |
| `DEEPSEEK_API_KEY` | ✅ Yes | DeepSeek API key for sentence generation |
| `TARGET_CHAT_IDS` | ✅ Yes* | Comma-separated list of student chat IDs |
| `REMINDER_CHAT_ID` | ❌ No | Your chat ID for Hebrew reminders |

*Or configure `TARGET_CHATS` list in code

---

## Deployment Checklist ✅

- [ ] VM set up with Python 3.10+
- [ ] Bot code uploaded
- [ ] `.env` file created with tokens
- [ ] Student chat IDs configured
- [ ] Virtual environment created (`python3 -m venv venv`)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Systemd service created
- [ ] Service enabled and started
- [ ] Tested with `/quiz` command
- [ ] Logs checked for errors

---

## Support 💬

For detailed deployment instructions, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

For issues with:
- Yandex Cloud VM setup → Check Yandex Cloud docs
- Telegram API → Check [Telegram Bot API docs](https://core.telegram.org/bots/api)
- DeepSeek API → Check [DeepSeek docs](https://platform.deepseek.com/docs)

---

## Version History 📋

- **v3.0** - Multiple student chats support with flexible configuration
- **v2.0** - Improved sentence variety with topic tracking
- **v1.0** - Initial release with single chat support

---

Made with ☕ for teaching Russian grammar 🇷🇺
