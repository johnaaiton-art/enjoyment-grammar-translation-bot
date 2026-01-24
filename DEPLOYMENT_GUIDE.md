# Elena Grammar Bot - Yandex Cloud Deployment Guide

## 📋 Overview
This guide will help you deploy the Elena Grammar Bot on your Yandex Cloud VM with systemd for automatic startup and management.

---

## 🚀 Initial Setup

### 1. Connect to Your VM
```bash
ssh your-username@your-vm-ip
```

### 2. Install Python and Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.10+ and pip
sudo apt install python3 python3-pip python3-venv -y

# Install git if needed
sudo apt install git -y
```

### 3. Create Application Directory
```bash
# Create directory for the bot
mkdir -p ~/bots/elena-grammar-bot
cd ~/bots/elena-grammar-bot
```

### 4. Upload Your Bot Code
Option A - Using scp from your local machine:
```bash
scp elena_grammar_bot.py your-username@your-vm-ip:~/bots/elena-grammar-bot/
```

Option B - Using git:
```bash
git clone your-repo-url .
```

Option C - Using nano/vim directly on VM:
```bash
nano elena_grammar_bot.py
# Paste the code, Ctrl+X, Y, Enter
```

---

## 🔧 Configuration

### 1. Set Up Environment Variables

Create a `.env` file:
```bash
nano ~/bots/elena-grammar-bot/.env
```

Add your configuration:
```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
DEEPSEEK_API_KEY=your_deepseek_key_here
REMINDER_CHAT_ID=your_chat_id_for_reminders

# Option 1: List chat IDs in .env (easiest for updates)
TARGET_CHAT_IDS=123456789,-987654321,111222333
# Format: comma-separated, no spaces around commas
# Negative numbers are group chats, positive are private chats

# Or Option 2: Edit TARGET_CHATS list directly in the Python file
```

**How to get Chat IDs:**
1. Add your bot to the chat/group
2. Send a message in the chat
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Look for `"chat":{"id":123456789}` in the JSON response

### 2. Create Python Virtual Environment
```bash
cd ~/bots/elena-grammar-bot
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies
```bash
pip install --upgrade pip
pip install python-telegram-bot requests apscheduler pytz python-dotenv
```

### 4. Test the Bot Manually
```bash
# Make sure venv is activated
source ~/bots/elena-grammar-bot/venv/bin/activate

# Load environment variables and run
python elena_grammar_bot.py
```

Test by sending `/start` and `/quiz` to your bot. Press Ctrl+C to stop.

---

## 🔄 Systemd Service Setup (Auto-Start on Boot)

### 1. Create Systemd Service File
```bash
sudo nano /etc/systemd/system/elena-grammar-bot.service
```

### 2. Add Service Configuration
```ini
[Unit]
Description=Elena Grammar Bot
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/bots/elena-grammar-bot
Environment="PATH=/home/your-username/bots/elena-grammar-bot/venv/bin"
EnvironmentFile=/home/your-username/bots/elena-grammar-bot/.env
ExecStart=/home/your-username/bots/elena-grammar-bot/venv/bin/python elena_grammar_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Important:** Replace `your-username` with your actual username (run `whoami` to check).

### 3. Enable and Start the Service
```bash
# Reload systemd to recognize new service
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable elena-grammar-bot.service

# Start the service now
sudo systemctl start elena-grammar-bot.service

# Check status
sudo systemctl status elena-grammar-bot.service
```

---

## 📊 Managing the Service

### Check Status
```bash
sudo systemctl status elena-grammar-bot.service
```

### View Logs
```bash
# Recent logs
sudo journalctl -u elena-grammar-bot.service -n 50

# Follow logs in real-time
sudo journalctl -u elena-grammar-bot.service -f

# Logs from today
sudo journalctl -u elena-grammar-bot.service --since today
```

### Restart Service
```bash
sudo systemctl restart elena-grammar-bot.service
```

### Stop Service
```bash
sudo systemctl stop elena-grammar-bot.service
```

### Disable Auto-Start
```bash
sudo systemctl disable elena-grammar-bot.service
```

---

## ✏️ Updating the Bot

### Option 1: Quick Update (Easiest)

**To add a new student chat:**
```bash
# Edit .env file
nano ~/bots/elena-grammar-bot/.env

# Add the new chat ID to TARGET_CHAT_IDS:
# OLD: TARGET_CHAT_IDS=123456789,-987654321
# NEW: TARGET_CHAT_IDS=123456789,-987654321,444555666

# Restart the service
sudo systemctl restart elena-grammar-bot.service

# Check it's running
sudo systemctl status elena-grammar-bot.service
```

### Option 2: Update Code

```bash
# Edit the Python file
nano ~/bots/elena-grammar-bot/elena_grammar_bot.py

# Find the TARGET_CHATS section and update:
TARGET_CHATS = [
    (123456789, "Elena"),
    (-987654321, "Maria"),
    (444555666, "Dmitry"),  # NEW STUDENT
]

# Restart the service
sudo systemctl restart elena-grammar-bot.service
```

### Option 3: Replace Entire File
```bash
# Stop service
sudo systemctl stop elena-grammar-bot.service

# Upload new version
scp elena_grammar_bot.py your-username@your-vm-ip:~/bots/elena-grammar-bot/

# Start service
sudo systemctl start elena-grammar-bot.service
```

---

## 🔍 Troubleshooting

### Bot Not Starting
```bash
# Check logs for errors
sudo journalctl -u elena-grammar-bot.service -n 100

# Common issues:
# 1. Wrong path in service file - check WorkingDirectory
# 2. Missing dependencies - activate venv and pip install again
# 3. Wrong .env file location or format
# 4. Invalid chat IDs
```

### Environment Variables Not Loading
```bash
# Check .env file exists
ls -la ~/bots/elena-grammar-bot/.env

# Check .env file contents (careful with sensitive data!)
cat ~/bots/elena-grammar-bot/.env

# Verify systemd can read it
sudo systemctl show elena-grammar-bot.service -p Environment
```

### Permission Issues
```bash
# Make sure your user owns the files
sudo chown -R your-username:your-username ~/bots/elena-grammar-bot/

# Make Python file executable (optional)
chmod +x ~/bots/elena-grammar-bot/elena_grammar_bot.py
```

### DeepSeek API Errors
```bash
# Check if API key is set correctly
grep DEEPSEEK .env

# Test API manually
curl -X POST https://api.deepseek.com/v1/chat/completions \
  -H "Authorization: Bearer YOUR_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"Hello"}]}'
```

---

## 🎯 Quick Reference: Adding New Students

### Method 1: Using .env (Recommended - No Code Changes)
1. Get chat ID from Telegram API
2. Edit `.env`: `nano ~/bots/elena-grammar-bot/.env`
3. Add ID to `TARGET_CHAT_IDS`: `TARGET_CHAT_IDS=old_ids,new_id`
4. Restart: `sudo systemctl restart elena-grammar-bot.service`
5. Check: `sudo journalctl -u elena-grammar-bot.service -n 20`

### Method 2: Editing Code
1. Get chat ID
2. Edit file: `nano ~/bots/elena-grammar-bot/elena_grammar_bot.py`
3. Add to `TARGET_CHATS` list: `(chat_id, "Student Name")`
4. Restart: `sudo systemctl restart elena-grammar-bot.service`

---

## 📱 Testing with New Students

1. Add student's chat ID using either method above
2. Restart service
3. Send `/start` to bot in student's chat
4. Use `/quiz` in YOUR private chat with the bot
5. Select sentences - they should go to ALL configured chats
6. Check logs if issues: `sudo journalctl -u elena-grammar-bot.service -f`

---

## 🔐 Security Notes

- Never commit `.env` file to git
- Keep your bot token secret
- Use `chmod 600 .env` to restrict file permissions
- Regularly update your VM: `sudo apt update && sudo apt upgrade`
- Consider using firewall rules to limit access

---

## 📝 File Structure on VM

```
~/bots/elena-grammar-bot/
├── elena_grammar_bot.py    # Main bot code
├── .env                     # Environment variables (create this)
├── venv/                    # Virtual environment (created by python3 -m venv)
│   ├── bin/
│   ├── lib/
│   └── ...
└── README.md               # This file (optional)
```

---

## 🎉 Done!

Your bot should now:
- ✅ Start automatically when VM boots
- ✅ Restart automatically if it crashes
- ✅ Send sentences to all configured student chats
- ✅ Send reminders at 10:00 and 16:00 UTC
- ✅ Log everything for debugging

Good luck with your teaching! 🚀
