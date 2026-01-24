# 🎯 COMPLETE DEPLOYMENT CHECKLIST
## Elena Grammar Bot - From Claude to Production

---

## 📥 PHASE 1: DOWNLOAD FILES TO YOUR PC

### Location on PC:
```
C:\Users\John\YandexDisk\Python\innovative vocab\AI magic\yandex\enjoyment_reminder
```

### Files to Download from Claude:
- [ ] `main.py` - The main bot code
- [ ] `requirements.txt` - Python dependencies
- [ ] `.gitignore` - Git ignore file (protects .env)
- [ ] `README.md` - Quick reference guide
- [ ] `DEPLOYMENT_GUIDE.md` - Full deployment guide
- [ ] `VM_DEPLOYMENT_STEPS.md` - VM-specific instructions
- [ ] `env_example` - Template for .env file
- [ ] `elena-grammar-bot.service` - Systemd service file
- [ ] `deploy_local.ps1` - PowerShell deployment script

### Download Instructions:
1. Claude has provided all files
2. Save each file to the folder above
3. **REPLACE ALL existing files** in that folder

---

## 🔐 PHASE 2: CREATE .ENV FILE (CRITICAL!)

### On Your PC:
```powershell
cd "C:\Users\John\YandexDisk\Python\innovative vocab\AI magic\yandex\enjoyment_reminder"
copy env_example .env
notepad .env
```

### Fill in Your Secrets:
```bash
TELEGRAM_BOT_TOKEN=your_actual_bot_token
DEEPSEEK_API_KEY=your_actual_deepseek_key
REMINDER_CHAT_ID=your_chat_id_for_reminders
TARGET_CHAT_IDS=123456789,-987654321
```

### ⚠️ IMPORTANT:
- [ ] `.env` file created
- [ ] All tokens filled in
- [ ] `.env` is NOT committed to git (it's in .gitignore)
- [ ] Keep `.env` backup somewhere safe

---

## 📤 PHASE 3: PUSH TO GITHUB

### Open PowerShell:
```powershell
cd "C:\Users\John\YandexDisk\Python\innovative vocab\AI magic\yandex\enjoyment_reminder"
```

### Option A: Use Deployment Script (Easiest)
```powershell
.\deploy_local.ps1
```
This script will:
- Check all files are present
- Verify .env exists
- Add, commit, and push to GitHub
- Guide you through the process

### Option B: Manual Commands
```powershell
# Initialize git if needed
git init
git branch -M main

# Add remote if not already added
git remote add origin https://github.com/johnaaiton-art/enjoyment-grammar-translation-bot.git

# Add files
git add .

# Commit
git commit -m "Update Elena Grammar Bot - Multiple students support"

# Push
git push -u origin main
```

### Verify on GitHub:
- [ ] Visit: https://github.com/johnaaiton-art/enjoyment-grammar-translation-bot
- [ ] Check files are updated
- [ ] Verify `.env` is NOT there (should be hidden by .gitignore)

---

## 🖥️ PHASE 4: DEPLOY TO YANDEX VM

### Step 1: Connect to VM
```bash
ssh yc-user@84.252.141.140
```

### Step 2: Navigate and Pull
```bash
cd ~/enjoyment_reminder

# Pull latest code
git pull origin main
```

**If folder doesn't exist yet:**
```bash
cd ~
git clone https://github.com/johnaaiton-art/enjoyment-grammar-translation-bot.git enjoyment_reminder
cd enjoyment_reminder
```

### Step 3: Create .env on VM
```bash
nano .env
```

**Copy your secrets from PC .env file and paste here:**
```bash
TELEGRAM_BOT_TOKEN=...
DEEPSEEK_API_KEY=...
REMINDER_CHAT_ID=...
TARGET_CHAT_IDS=...
```

**Save**: `Ctrl+X`, `Y`, `Enter`

### Step 4: Set Up Python Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5: Test Bot Manually (Optional)
```bash
# Make sure venv is activated
source venv/bin/activate

# Run bot
python main.py

# Test with /start and /quiz in Telegram
# Press Ctrl+C to stop
```

### Step 6: Set Up Systemd Service
```bash
# Copy service file
sudo cp elena-grammar-bot.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start service
sudo systemctl enable elena-grammar-bot.service
sudo systemctl start elena-grammar-bot.service

# Check status
sudo systemctl status elena-grammar-bot.service
```

**Expected**: Should show "active (running)" in green

### Step 7: Monitor Logs
```bash
# View recent logs
sudo journalctl -u elena-grammar-bot.service -n 50

# Follow live logs (Ctrl+C to stop)
sudo journalctl -u elena-grammar-bot.service -f
```

---

## ✅ PHASE 5: VERIFICATION

### Test Bot Functionality:
- [ ] Send `/start` to bot - gets welcome message
- [ ] Send `/quiz` to bot - receives 6 sentence buttons
- [ ] Click a sentence button - confirmation it was sent
- [ ] Check student chats - sentence appears in all configured chats
- [ ] Wait 30 seconds - buttons should expire

### Test Reminders:
- [ ] Reminders send at 10:00 UTC (if REMINDER_CHAT_ID is set)
- [ ] Reminders send at 16:00 UTC

### Check Service:
- [ ] Service is running: `sudo systemctl status elena-grammar-bot.service`
- [ ] No errors in logs: `sudo journalctl -u elena-grammar-bot.service -n 100`
- [ ] Service survives reboot: `sudo reboot` then check again

---

## 🔄 FUTURE UPDATES QUICK GUIDE

### When You Update Code:

#### On PC:
```powershell
cd "C:\Users\John\YandexDisk\Python\innovative vocab\AI magic\yandex\enjoyment_reminder"

# Edit files as needed
# ...

# Push to GitHub
git add .
git commit -m "Update: description of changes"
git push origin main
```

#### On VM:
```bash
ssh yc-user@84.252.141.140
cd ~/enjoyment_reminder
git pull origin main
sudo systemctl restart elena-grammar-bot.service
sudo systemctl status elena-grammar-bot.service
```

### When You Add New Student:
```bash
ssh yc-user@84.252.141.140
cd ~/enjoyment_reminder
nano .env
# Add new chat ID to TARGET_CHAT_IDS
sudo systemctl restart elena-grammar-bot.service
```

---

## 🆘 TROUBLESHOOTING CHECKLIST

### Bot Not Starting:
- [ ] Check logs: `sudo journalctl -u elena-grammar-bot.service -n 100`
- [ ] Verify .env exists: `ls -la ~/enjoyment_reminder/.env`
- [ ] Check .env format: `cat ~/enjoyment_reminder/.env`
- [ ] Test manually: `cd ~/enjoyment_reminder && source venv/bin/activate && python main.py`

### Bot Not Responding:
- [ ] Service running: `sudo systemctl status elena-grammar-bot.service`
- [ ] Check live logs: `sudo journalctl -u elena-grammar-bot.service -f`
- [ ] Restart: `sudo systemctl restart elena-grammar-bot.service`

### Git Issues:
- [ ] Check remote: `git remote -v`
- [ ] Reset remote: `git remote remove origin && git remote add origin <url>`
- [ ] Force pull: `git fetch --all && git reset --hard origin/main`

### Sentences Too Repetitive:
- Bot tracks topics automatically
- Temperature is 0.9 for variety
- If still repetitive, restart service: `sudo systemctl restart elena-grammar-bot.service`

---

## 📞 QUICK REFERENCE COMMANDS

### VM Access:
```bash
ssh yc-user@84.252.141.140
```

### Navigate to Project:
```bash
cd ~/enjoyment_reminder
```

### Service Management:
```bash
sudo systemctl start elena-grammar-bot.service
sudo systemctl stop elena-grammar-bot.service
sudo systemctl restart elena-grammar-bot.service
sudo systemctl status elena-grammar-bot.service
```

### View Logs:
```bash
sudo journalctl -u elena-grammar-bot.service -f
sudo journalctl -u elena-grammar-bot.service -n 50
```

### Update from GitHub:
```bash
cd ~/enjoyment_reminder
git pull origin main
sudo systemctl restart elena-grammar-bot.service
```

---

## 🎉 DEPLOYMENT COMPLETE!

When all checkboxes are ticked, your bot is:
- ✅ Running 24/7 on Yandex Cloud
- ✅ Auto-starting on VM reboot
- ✅ Sending to multiple student chats
- ✅ Generating varied Russian sentences
- ✅ Easy to update via git pull

**Enjoy teaching Russian grammar!** 🇷🇺📚
