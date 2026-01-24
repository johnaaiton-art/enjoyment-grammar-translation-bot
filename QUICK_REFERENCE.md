# ⚡ QUICK REFERENCE CARD
## Elena Grammar Bot - Common Commands

---

## 🔌 CONNECT TO VM
```bash
ssh yc-user@84.252.141.140
cd ~/enjoyment_reminder
```

---

## 📊 CHECK BOT STATUS
```bash
# Is it running?
sudo systemctl status elena-grammar-bot.service

# View recent logs
sudo journalctl -u elena-grammar-bot.service -n 50

# Follow live logs
sudo journalctl -u elena-grammar-bot.service -f
```

---

## 🔄 SERVICE CONTROL
```bash
# Start bot
sudo systemctl start elena-grammar-bot.service

# Stop bot
sudo systemctl stop elena-grammar-bot.service

# Restart bot
sudo systemctl restart elena-grammar-bot.service

# Enable auto-start on boot
sudo systemctl enable elena-grammar-bot.service
```

---

## 🆕 ADD NEW STUDENT

**Step 1**: Get chat ID
- Add bot to chat
- Send message
- Visit: `https://api.telegram.org/bot<TOKEN>/getUpdates`
- Find: `"chat":{"id":123456789}`

**Step 2**: Update config
```bash
ssh yc-user@84.252.141.140
cd ~/enjoyment_reminder
nano .env
```

**Step 3**: Add ID to TARGET_CHAT_IDS
```bash
# Old: TARGET_CHAT_IDS=123456789,-987654321
# New: TARGET_CHAT_IDS=123456789,-987654321,444555666
```

**Step 4**: Restart
```bash
sudo systemctl restart elena-grammar-bot.service
sudo systemctl status elena-grammar-bot.service
```

---

## 🔄 UPDATE BOT CODE

**On PC**:
```powershell
cd "C:\Users\John\YandexDisk\Python\innovative vocab\AI magic\yandex\enjoyment_reminder"
git add .
git commit -m "Update: description"
git push origin main
```

**On VM**:
```bash
ssh yc-user@84.252.141.140
cd ~/enjoyment_reminder
git pull origin main
sudo systemctl restart elena-grammar-bot.service
```

---

## 🐛 TROUBLESHOOTING

**Bot not responding?**
```bash
sudo systemctl status elena-grammar-bot.service
sudo journalctl -u elena-grammar-bot.service -n 100
sudo systemctl restart elena-grammar-bot.service
```

**Check .env file:**
```bash
cat ~/enjoyment_reminder/.env
```

**Test manually:**
```bash
cd ~/enjoyment_reminder
source venv/bin/activate
python main.py
# Press Ctrl+C to stop
```

---

## 📱 TELEGRAM COMMANDS

Send to your bot:
- `/start` - Initialize bot
- `/quiz` - Get 6 practice sentences
- Click buttons to send to students

---

## 📂 FILE LOCATIONS

**PC Folder:**
```
C:\Users\John\YandexDisk\Python\innovative vocab\AI magic\yandex\enjoyment_reminder
```

**VM Folder:**
```
/home/yc-user/enjoyment_reminder
```

**Service File:**
```
/etc/systemd/system/elena-grammar-bot.service
```

---

## 🔑 IMPORTANT FILES

- `main.py` - Bot code
- `.env` - Your secrets (NOT in git!)
- `requirements.txt` - Dependencies
- `.gitignore` - Protects .env
- `elena-grammar-bot.service` - Systemd config

---

## 📝 ENVIRONMENT VARIABLES

In `.env` file:
```bash
TELEGRAM_BOT_TOKEN=your_token
DEEPSEEK_API_KEY=your_key
REMINDER_CHAT_ID=your_chat_id
TARGET_CHAT_IDS=id1,id2,id3
```

---

## ⚠️ REMEMBER

- ✅ `.env` never goes to GitHub
- ✅ Always `git pull` before restart
- ✅ Check logs after changes
- ✅ Positive IDs = private chats
- ✅ Negative IDs = group chats

---

## 🔗 GITHUB REPO
https://github.com/johnaaiton-art/enjoyment-grammar-translation-bot

---

## 📞 VM INFO

**IP**: 84.252.141.140
**User**: yc-user
**Folder**: ~/enjoyment_reminder
**Service**: elena-grammar-bot.service

---

**Keep this card handy for quick operations!** 🚀
