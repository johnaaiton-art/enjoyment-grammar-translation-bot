# ============================================
# ELENA GRAMMAR BOT - LOCAL DEPLOYMENT SCRIPT
# ============================================
# This script helps you download files and push to GitHub
# Run from PowerShell in: C:\Users\John\YandexDisk\Python\innovative vocab\AI magic\yandex\enjoyment_reminder

# IMPORTANT: Make sure you have .env file with your secrets!
# The .env file should NOT be in git (it's in .gitignore)

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "ELENA GRAMMAR BOT - Deployment Script" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if we're in the right directory
$expectedPath = "C:\Users\John\YandexDisk\Python\innovative vocab\AI magic\yandex\enjoyment_reminder"
$currentPath = Get-Location

if ($currentPath.Path -ne $expectedPath) {
    Write-Host "WARNING: You should run this from:" -ForegroundColor Yellow
    Write-Host $expectedPath -ForegroundColor Yellow
    Write-Host "`nCurrent location: $($currentPath.Path)" -ForegroundColor Red
    $continue = Read-Host "`nContinue anyway? (y/n)"
    if ($continue -ne 'y') {
        exit
    }
}

Write-Host "Step 1: Checking files..." -ForegroundColor Green

# List of required files
$requiredFiles = @(
    "main.py",
    "requirements.txt",
    ".gitignore",
    "README.md",
    "DEPLOYMENT_GUIDE.md",
    "env_example",
    "elena-grammar-bot.service"
)

$missingFiles = @()
foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host "`nMISSING FILES:" -ForegroundColor Red
    foreach ($file in $missingFiles) {
        Write-Host "  - $file" -ForegroundColor Red
    }
    Write-Host "`nPlease download these files from Claude and place them in this folder." -ForegroundColor Yellow
    exit
}

Write-Host "✓ All required files present`n" -ForegroundColor Green

# Check for .env file
Write-Host "Step 2: Checking .env file..." -ForegroundColor Green
if (-not (Test-Path ".env")) {
    Write-Host "WARNING: No .env file found!" -ForegroundColor Yellow
    Write-Host "You need to create .env file with your secrets." -ForegroundColor Yellow
    Write-Host "Use env_example as template.`n" -ForegroundColor Yellow
    
    $createEnv = Read-Host "Create .env now from env_example? (y/n)"
    if ($createEnv -eq 'y') {
        Copy-Item "env_example" ".env"
        Write-Host "✓ Created .env file - EDIT IT with your actual tokens!`n" -ForegroundColor Green
        notepad .env
    }
} else {
    Write-Host "✓ .env file exists (make sure it has valid tokens)`n" -ForegroundColor Green
}

# Git operations
Write-Host "Step 3: Git operations..." -ForegroundColor Green

# Check if git is initialized
if (-not (Test-Path ".git")) {
    Write-Host "Initializing git repository..." -ForegroundColor Yellow
    git init
    git branch -M main
}

# Check git status
Write-Host "`nCurrent git status:" -ForegroundColor Cyan
git status

Write-Host "`n---`n"
$proceed = Read-Host "Proceed with git add, commit, and push? (y/n)"

if ($proceed -eq 'y') {
    # Add files (excluding .env because of .gitignore)
    Write-Host "`nAdding files to git..." -ForegroundColor Yellow
    git add .
    
    # Commit
    $commitMsg = Read-Host "Enter commit message (or press Enter for default)"
    if ([string]::IsNullOrWhiteSpace($commitMsg)) {
        $commitMsg = "Update Elena Grammar Bot - $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
    }
    
    Write-Host "Committing with message: $commitMsg" -ForegroundColor Yellow
    git commit -m $commitMsg
    
    # Check if remote exists
    $remoteExists = git remote | Select-String "origin"
    if (-not $remoteExists) {
        Write-Host "`nAdding remote repository..." -ForegroundColor Yellow
        git remote add origin https://github.com/johnaaiton-art/enjoyment-grammar-translation-bot.git
    }
    
    # Push
    Write-Host "`nPushing to GitHub..." -ForegroundColor Yellow
    git push -u origin main
    
    Write-Host "`n✓ Successfully pushed to GitHub!`n" -ForegroundColor Green
    
} else {
    Write-Host "`nSkipped git operations.`n" -ForegroundColor Yellow
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "NEXT STEPS:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "1. ✓ Files are on GitHub (if you pushed)" -ForegroundColor White
Write-Host "2. Now pull to your Yandex VM:" -ForegroundColor White
Write-Host "`n   ssh yc-user@84.252.141.140" -ForegroundColor Yellow
Write-Host "   cd ~/enjoyment_reminder" -ForegroundColor Yellow
Write-Host "   git pull origin main`n" -ForegroundColor Yellow
Write-Host "3. See VM_DEPLOYMENT_STEPS.md for full VM setup`n" -ForegroundColor White

Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
