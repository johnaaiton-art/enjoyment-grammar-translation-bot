# VM DEPLOYMENT STEPS - YANDEX CLOUD
## For Elena Grammar Bot on enjoyment_reminder folder

---

## 📍 PREREQUISITE: Files Must Be on GitHub First!

Before starting, make sure you've:
1. ✅ Downloaded all files to your PC folder: `C:\Users\John\YandexDisk\Python\innovative vocab\AI magic\yandex\enjoyment_reminder`
2. ✅ Created `.env` file with your secrets (don't commit it!)
3. ✅ Run `deploy_local.ps1` in PowerShell to push to GitHub

---

## 🚀 STEP-BY-STEP VM DEPLOYMENT

### Step 1: Connect to Your VM
```bash
ssh yc-user@84.252.141.140
```

### Step 2: Navigate to Project Folder
```bash
cd ~/enjoyment_reminder
```

### Step 3: Check Current Git Status
```bash
git status
git remote -v
```

**If git is not initialized yet:**
```bash
git init
git remote add origin https://github.com/johnaaiton-art/enjoyment-grammar-translation-bot.git
git branch -M main
```

### Step 4: Pull Latest Code from GitHub
```bash
git pull origin main
```

**If you get errors about local changes:**
```bash
# Backup your current .env file first!
cp .env .env.backup

# Force pull (WARNING: This will overwrite local changes)
git fetch --all
git reset --hard origin/main

# Restore your .env file
cp .env.backup .env
```

### Step 5: Create/Update .env File
**IMPORTANT**: The `.env` file is NOT in git (for security). You must create it manually.

```bash
nano .env
```

Add your configuration:
```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
DEEPSEEK_API_KEY=your_deepseek_key_here
REMINDER_CHAT_ID=your_chat_id_for_reminders

# Add student chat IDs (comma-separated, no spaces)
TARGET_CHAT_IDS=123456789,-987654321,111222333
```

**Save and exit**: `Ctrl+X`, then `Y`, then `Enter`

### Step 6: Set Up Python Virtual Environment
```bash
# Create venv if it doesn't exist
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install/update dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 7: Test the Bot Manually (Optional but Recommended)
```bash
# Make sure venv is activated (you should see (venv) in prompt)
source venv/bin/activate

# Run the bot
python main.py
```

**Test it**: Send `/start` and `/quiz` to your bot in Telegram.
**Stop it**: Press `Ctrl+C`

### Step 8: Set Up Systemd Service

#### A. Copy Service File
```bash
sudo cp elena-grammar-bot.service /etc/systemd/system/
```

#### B. Edit Service File (if needed)
Check if paths are correct:
```bash
sudo nano /etc/systemd/system/elena-grammar-bot.service
```

Should have:
```ini
WorkingDirectory=/home/yc-user/enjoyment_reminder
EnvironmentFile=/home/yc-user/enjoyment_reminder/.env
ExecStart=/home/yc-user/enjoyment_reminder/venv/bin/python main.py
```

Save and exit: `Ctrl+X`, `Y`, `Enter`

#### C. Reload Systemd and Enable Service
```bash
# Reload systemd daemon
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable elena-grammar-bot.service

# Start the service
sudo systemctl start elena-grammar-bot.service

# Check status
sudo systemctl status elena-grammar-bot.service
```

**Expected output**: Should show "active (running)" in green.

#### D. View Logs
```bash
# Recent logs
sudo journalctl -u elena-grammar-bot.service -n 50

# Follow live logs (press Ctrl+C to stop)
sudo journalctl -u elena-grammar-bot.service -f
```

---

## ✅ VERIFICATION CHECKLIST

After deployment, verify:

- [ ] Service is running: `sudo systemctl status elena-grammar-bot.service`
- [ ] No errors in logs: `sudo journalctl -u elena-grammar-bot.service -n 50`
- [ ] Bot responds to `/start` in Telegram
- [ ] `/quiz` generates 6 sentences
- [ ] Clicking sentence buttons sends to configured chats
- [ ] Check logs show successful sends: `sudo journalctl -u elena-grammar-bot.service -f`

---

## 🔄 FUTURE UPDATES WORKFLOW

When you update the bot code:

### On Your PC:
```powershell
cd "C:\Users\John\YandexDisk\Python\innovative vocab\AI magic\yandex\enjoyment_reminder"

# Edit files as needed
# Run deployment script
.\deploy_local.ps1
```

### On VM:
```bash
ssh yc-user@84.252.141.140
cd ~/enjoyment_reminder
git pull origin main
sudo systemctl restart elena-grammar-bot.service
sudo systemctl status elena-grammar-bot.service
```

---

## 🆕 ADDING NEW STUDENT CHATS

### Easy Method - Edit .env on VM:
```bash
ssh yc-user@84.252.141.140
cd ~/enjoyment_reminder
nano .env

# Update this line:
TARGET_CHAT_IDS=123456789,-987654321,444555666
#                                    ^ add new ID

# Save (Ctrl+X, Y, Enter)

# Restart service
sudo systemctl restart elena-grammar-bot.service
```

### How to Get Chat ID:
1. Add bot to the chat
2. Send a message in that chat
3. Visit in browser: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Find: `"chat":{"id":123456789}`
5. Copy that number

---

## 🛠️ TROUBLESHOOTING

### Service Won't Start
```bash
# Check detailed logs
sudo journalctl -u elena-grammar-bot.service -n 100

# Check if .env file exists
ls -la ~/enjoyment_reminder/.env

# Check .env format (no extra spaces, quotes, etc.)
cat ~/enjoyment_reminder/.env

# Try running manually to see error
cd ~/enjoyment_reminder
source venv/bin/activate
python main.py
```

### Bot Not Responding
```bash
# Is service running?
sudo systemctl status elena-grammar-bot.service

# View live logs
sudo journalctl -u elena-grammar-bot.service -f

# Restart service
sudo systemctl restart elena-grammar-bot.service
```

### "Permission Denied" Errors
```bash
# Fix ownership
sudo chown -R yc-user:yc-user ~/enjoyment_reminder/

# Fix .env permissions
chmod 600 ~/enjoyment_reminder/.env
```

### Can't Pull from GitHub
```bash
# Check remote
git remote -v

# If wrong, remove and re-add
git remote remove origin
git remote add origin https://github.com/johnaaiton-art/enjoyment-grammar-translation-bot.git

# Pull again
git pull origin main
```

---

## 📝 QUICK REFERENCE

### Service Commands
```bash
sudo systemctl start elena-grammar-bot.service    # Start
sudo systemctl stop elena-grammar-bot.service     # Stop
sudo systemctl restart elena-grammar-bot.service  # Restart
sudo systemctl status elena-grammar-bot.service   # Status
sudo systemctl enable elena-grammar-bot.service   # Enable on boot
sudo systemctl disable elena-grammar-bot.service  # Disable on boot
```

### Log Commands
```bash
sudo journalctl -u elena-grammar-bot.service -f      # Follow logs
sudo journalctl -u elena-grammar-bot.service -n 50   # Last 50 lines
sudo journalctl -u elena-grammar-bot.service --since "1 hour ago"
sudo journalctl -u elena-grammar-bot.service --since today
```

---

## 🎉 DONE!

Your bot should now be running 24/7 on your Yandex VM!

Test it by:
1. Sending `/quiz` to the bot
2. Selecting sentences
3. Checking they arrive in all configured student chats

Good luck with your grammar teaching! 🇷🇺📚
