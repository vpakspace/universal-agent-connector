# PowerShell script to setup all demo projects
# Creates databases and loads sample data

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Setting up all demo projects" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Get database credentials
$DB_USER = Read-Host "PostgreSQL username [postgres]"
if ([string]::IsNullOrEmpty($DB_USER)) { $DB_USER = "postgres" }

$DB_PASSWORD = Read-Host "PostgreSQL password" -AsSecureString
$DB_PASSWORD_PLAIN = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($DB_PASSWORD)
)

$DB_HOST = Read-Host "PostgreSQL host [localhost]"
if ([string]::IsNullOrEmpty($DB_HOST)) { $DB_HOST = "localhost" }

$DB_PORT = Read-Host "PostgreSQL port [5432]"
if ([string]::IsNullOrEmpty($DB_PORT)) { $DB_PORT = "5432" }

# Set environment variable for psql
$env:PGPASSWORD = $DB_PASSWORD_PLAIN

# Function to setup a demo
function Setup-Demo {
    param(
        [string]$DemoName,
        [string]$DbName,
        [string]$SetupFile
    )
    
    Write-Host "Setting up $DemoName..." -ForegroundColor Blue
    
    # Check if database exists
    $dbExists = psql -h $DB_HOST -p $DB_PORT -U $DB_USER -lqt | Select-String -Pattern "\b$DbName\b"
    
    if ($dbExists) {
        Write-Host "  Database $DbName already exists. Dropping..." -ForegroundColor Yellow
        psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "DROP DATABASE IF EXISTS $DbName;"
    }
    
    Write-Host "  Creating database $DbName..."
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "CREATE DATABASE $DbName;"
    
    Write-Host "  Loading sample data..."
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DbName -f $SetupFile
    
    Write-Host "✓ $DemoName setup complete!" -ForegroundColor Green
    Write-Host ""
}

# Setup each demo
Setup-Demo "E-Commerce Demo" "ecommerce_demo" "demos\ecommerce\setup.sql"
Setup-Demo "SaaS Metrics Demo" "saas_demo" "demos\saas\setup.sql"
Setup-Demo "Financial Reporting Demo" "financial_demo" "demos\financial\setup.sql"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "All demos setup complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Start AI Agent Connector: python main.py"
Write-Host "2. Visit http://localhost:5000/dashboard"
Write-Host "3. Follow the demo walkthroughs:"
Write-Host "   - demos\ecommerce\WALKTHROUGH.md"
Write-Host "   - demos\saas\WALKTHROUGH.md"
Write-Host "   - demos\financial\WALKTHROUGH.md"
Write-Host ""

# Clean up
Remove-Item Env:\PGPASSWORD

