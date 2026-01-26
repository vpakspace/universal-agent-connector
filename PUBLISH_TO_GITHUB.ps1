# PowerShell script to publish Universal Agent Connector to GitHub
# Run this script after creating the repository on GitHub

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Universal Agent Connector - GitHub Publish" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if git is initialized
if (-not (Test-Path ".git")) {
    Write-Host "Initializing git repository..." -ForegroundColor Yellow
    git init
    git checkout -b main
} else {
    Write-Host "Git repository already initialized" -ForegroundColor Green
}

# Check current branch
$currentBranch = git branch --show-current
Write-Host "Current branch: $currentBranch" -ForegroundColor Cyan

# Check if remote exists
$remoteExists = git remote | Select-String -Pattern "origin"
if (-not $remoteExists) {
    Write-Host ""
    Write-Host "No remote 'origin' found. Please add it manually:" -ForegroundColor Yellow
    Write-Host "  git remote add origin https://github.com/cloudbadal007/universal-agent-connector.git" -ForegroundColor White
    Write-Host ""
    Write-Host "Or if you want to add it now, enter 'y' to continue:" -ForegroundColor Yellow
    $response = Read-Host
    if ($response -eq 'y' -or $response -eq 'Y') {
        git remote add origin https://github.com/cloudbadal007/universal-agent-connector.git
        Write-Host "Remote 'origin' added successfully!" -ForegroundColor Green
    }
} else {
    Write-Host "Remote 'origin' already exists" -ForegroundColor Green
    git remote -v
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 1: Add all files" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Adding all files to staging..." -ForegroundColor Yellow
git add .

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 2: Check status" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
git status

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 3: Create initial commit" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Creating initial commit..." -ForegroundColor Yellow

$commitMessage = @"
Initial commit: Universal Agent Connector v1.0.0

- Core agent registry and authentication
- Multi-database support (PostgreSQL, MySQL, MongoDB, BigQuery, Snowflake)
- Fine-grained permission system
- Natural language to SQL conversion
- MCP semantic routing with ontology support
- Universal Ontology Adapter
- Enterprise features (SSO, audit, chargeback)
- Complete documentation and deployment guides
"@

git commit -m $commitMessage

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 4: Push to GitHub" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "IMPORTANT: Make sure you have:" -ForegroundColor Yellow
Write-Host "  1. Created the repository on GitHub: https://github.com/cloudbadal007/universal-agent-connector" -ForegroundColor White
Write-Host "  2. Set it as Public" -ForegroundColor White
Write-Host "  3. Added the description and topics" -ForegroundColor White
Write-Host ""
Write-Host "Ready to push? (y/n): " -ForegroundColor Yellow -NoNewline
$pushResponse = Read-Host

if ($pushResponse -eq 'y' -or $pushResponse -eq 'Y') {
    Write-Host ""
    Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
    git push -u origin main
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "Successfully pushed to GitHub!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Cyan
        Write-Host "  1. Create 'develop' branch: git checkout -b develop && git push -u origin develop" -ForegroundColor White
        Write-Host "  2. Configure repository settings on GitHub" -ForegroundColor White
        Write-Host "  3. Add repository topics" -ForegroundColor White
        Write-Host "  4. Upload social preview image (1280x640px)" -ForegroundColor White
        Write-Host ""
        Write-Host "Repository URL: https://github.com/cloudbadal007/universal-agent-connector" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "Push failed. Please check:" -ForegroundColor Red
        Write-Host "  - Repository exists on GitHub" -ForegroundColor White
        Write-Host "  - You have push permissions" -ForegroundColor White
        Write-Host "  - Authentication is set up (GitHub CLI or SSH keys)" -ForegroundColor White
    }
} else {
    Write-Host ""
    Write-Host "Push cancelled. Run this script again when ready." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Done!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
