# 🚀 START HERE - COMPLETE DEPLOYMENT INSTRUCTIONS
## Elena Grammar Bot: From Download to Production

---

## 📋 WHAT YOU'RE DEPLOYING

A Telegram bot that:
- Generates 6 Russian grammar practice sentences on demand
- Sends them to multiple student chats simultaneously
- Uses AI (DeepSeek) for varied, natural examples
- Sends Hebrew reminder messages twice daily
- Runs 24/7 on your Yandex Cloud VM

---

## 📥 STEP 1: DOWNLOAD ALL FILES TO YOUR PC

### Target Folder:
```
C:\Users\John\YandexDisk\Python\innovative vocab\AI magic\yandex\enjoyment_reminder
```

### Files to Download (10 files total):

1. **main.py** - The bot code (REPLACES existing main.py)
2. **requirements.txt** - Python dependencies
3. **.gitignore** - Protects your secrets from git
4. **README.md** - Quick reference
5. **DEPLOYMENT_GUIDE.md** - Full technical guide
6. **VM_DEPLOYMENT_STEPS.md** - VM-specific instructions
7. **DEPLOYMENT_CHECKLIST.md** - Complete checklist
8. **env_example** - Template for .env file
9. **elena-grammar-bot.service** - Systemd service file
10. **deploy_local.ps1** - PowerShell deployment script

### How to Download:
Claude has provided all these files above. Download each one and save to your folder.
**REPLACE ALL existing files** - these are updated versions.

---

## 🔐 STEP 2: CREATE YOUR .ENV FILE

**CRITICAL**: Never commit this file to git!

### In Your PC Folder:
```powershell
cd "C:\Users\John\YandexDisk\Python\innovative vocab\AI magic\yandex\enjoyment_reminder"
copy env_example .env
notepad .env
```

### Fill In Your Actual Values:
```bash
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz-REAL_TOKEN
DEEPSEEK_API_KEY=sk-XXXXXXXXXXXXXXXXXXXXX-REAL_KEY
REMINDER_CHAT_ID=123456789
TARGET_CHAT_IDS=123456789,-987654321,111222333
```

### Getting Chat IDs:
1. Add bot to chat
2. Send a message
3. Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
4. Find `"chat":{"id":123456789}`

**Save the file!**

---

## 📤 STEP 3: PUSH TO GITHUB

### Open PowerShell as Administrator:
```powershell
cd "C:\Users\John\YandexDisk\Python\innovative vocab\AI magic\yandex\enjoyment_reminder"
```

### Run the Deployment Script:
```powershell
.\deploy_local.ps1
```

The script will:
- ✅ Check all files are present
- ✅ Verify .env exists (but won't commit it)
- ✅ Initialize git if needed
- ✅ Add files to git
- ✅ Commit with timestamp
- ✅ Push to: https://github.com/johnaaiton-art/enjoyment-grammar-translation-bot

### OR Manual Commands:
```powershell
git init
git branch -M main
git remote add origin https://github.com/johnaaiton-art/enjoyment-grammar-translation-bot.git
git add .
git commit -m "Update Elena Grammar Bot - Multi-student support"
git push -u origin main
```

### Verify on GitHub:
Visit your repo and confirm files are updated (except .env which should NOT be there).

---

## 🖥️ STEP 4: DEPLOY TO YANDEX VM

### Connect to VM:
```bash
ssh yc-user@84.252.141.140
```

### Navigate to Folder:
```bash
cd ~/enjoyment_reminder
```

**If folder doesn't exist:**
```bash
cd ~
git clone https://github.com/johnaaiton-art/enjoyment-grammar-translation-bot.git enjoyment_reminder
cd enjoyment_reminder
```

### Pull Latest Code:
```bash
git pull origin main
```

### Create .env on VM:
```bash
nano .env
```

**Paste your secrets from PC .env file:**
```bash
TELEGRAM_BOT_TOKEN=...
DEEPSEEK_API_KEY=...
REMINDER_CHAT_ID=...
TARGET_CHAT_IDS=...
```

**Save**: Press `Ctrl+X`, then `Y`, then `Enter`

### Install Dependencies:
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install packages
pip install --upgrade pip
pip install -r requirements.txt
```

### Set Up Systemd Service:
```bash
# Copy service file
sudo cp elena-grammar-bot.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service (auto-start on boot)
sudo systemctl enable elena-grammar-bot.service

# Start service now
sudo systemctl start elena-grammar-bot.service

# Check it's running
sudo systemctl status elena-grammar-bot.service
```

**Should show**: "active (running)" in green

### Monitor Logs:
```bash
# View recent logs
sudo journalctl -u elena-grammar-bot.service -n 50

# Follow live (press Ctrl+C to stop)
sudo journalctl -u elena-grammar-bot.service -f
```

---

## ✅ STEP 5: TEST THE BOT

### In Telegram:
1. Send `/start` to your bot
2. Send `/quiz` to your bot
3. You should get 6 Russian sentence buttons
4. Click a sentence
5. Check that sentence appears in ALL configured student chats
6. Check logs on VM show successful sends

### Expected Behavior:
- Buttons work for 30 seconds
- Each click sends to all chats in TARGET_CHAT_IDS
- You get confirmation message
- Logs show: "Sentence X sent to Student_1 (123456789)"

---

## 🔄 FUTURE UPDATES - QUICK GUIDE

### Update Bot Code:

**On PC:**
```powershell
cd "C:\Users\John\YandexDisk\Python\innovative vocab\AI magic\yandex\enjoyment_reminder"
# Edit main.py or other files
git add .
git commit -m "Update: your changes"
git push origin main
```

**On VM:**
```bash
ssh yc-user@84.252.141.140
cd ~/enjoyment_reminder
git pull origin main
sudo systemctl restart elena-grammar-bot.service
sudo systemctl status elena-grammar-bot.service
```

### Add New Student:
```bash
ssh yc-user@84.252.141.140
cd ~/enjoyment_reminder
nano .env
# Update TARGET_CHAT_IDS line with new ID
sudo systemctl restart elena-grammar-bot.service
```

---

## 🆘 TROUBLESHOOTING

### Bot Not Starting?
```bash
# Check logs for errors
sudo journalctl -u elena-grammar-bot.service -n 100

# Common fixes:
# 1. Check .env exists and has correct values
ls -la ~/enjoyment_reminder/.env
cat ~/enjoyment_reminder/.env

# 2. Try running manually to see error
cd ~/enjoyment_reminder
source venv/bin/activate
python main.py
```

### Can't Push to GitHub?
```powershell
# Check if remote is correct
git remote -v

# Should show: https://github.com/johnaaiton-art/enjoyment-grammar-translation-bot.git

# If not, fix it:
git remote remove origin
git remote add origin https://github.com/johnaaiton-art/enjoyment-grammar-translation-bot.git
git push -u origin main
```

### Service Won't Start on VM?
```bash
# Check service file
sudo systemctl status elena-grammar-bot.service

# View detailed errors
sudo journalctl -xe -u elena-grammar-bot.service

# Verify paths in service file
sudo nano /etc/systemd/system/elena-grammar-bot.service

# Should have:
# WorkingDirectory=/home/yc-user/enjoyment_reminder
# ExecStart=/home/yc-user/enjoyment_reminder/venv/bin/python main.py
```

---

## 📚 DOCUMENTATION FILES

After setup, you have these guides:

1. **DEPLOYMENT_CHECKLIST.md** - Complete step-by-step checklist
2. **VM_DEPLOYMENT_STEPS.md** - VM-specific detailed instructions
3. **DEPLOYMENT_GUIDE.md** - Full technical documentation
4. **README.md** - Quick reference and feature list

Read them for more details!

---

## 🎯 QUICK COMMAND REFERENCE

### VM Access:
```bash
ssh yc-user@84.252.141.140
cd ~/enjoyment_reminder
```

### Service Commands:
```bash
sudo systemctl start elena-grammar-bot.service
sudo systemctl stop elena-grammar-bot.service
sudo systemctl restart elena-grammar-bot.service
sudo systemctl status elena-grammar-bot.service
```

### Logs:
```bash
sudo journalctl -u elena-grammar-bot.service -f
```

### Update from GitHub:
```bash
git pull origin main
sudo systemctl restart elena-grammar-bot.service
```

---

## ✨ YOU'RE DONE!

After completing all steps, your bot:
- ✅ Runs 24/7 on Yandex Cloud
- ✅ Auto-starts on VM reboot
- ✅ Sends to multiple students simultaneously
- ✅ Generates varied Russian sentences
- ✅ Easy to update via GitHub
- ✅ Protected secrets (not in git)

**Start with STEP 1 above and follow each step in order!**

Good luck! 🚀🇷🇺📚
