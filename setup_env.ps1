# PowerShell script to set up environment variables for Bot Doc

Write-Host "Setting up environment variables for Bot Doc..." -ForegroundColor Green

# Get the current directory
$currentDir = Get-Location

# Set environment variables for current session
$env:GOOGLE_APPLICATION_CREDENTIALS = Join-Path $currentDir "bot-doc-473208-706e6adceee1.json"
$env:PROJECT_ID = "bot-doc-473208"
$env:GOOGLE_CLOUD_LOCATION = "asia-southeast1"
$env:FIRESTORE_DATABASE = "default"

Write-Host "Environment variables set for current session:" -ForegroundColor Yellow
Write-Host "GOOGLE_APPLICATION_CREDENTIALS = $env:GOOGLE_APPLICATION_CREDENTIALS"
Write-Host "PROJECT_ID = $env:PROJECT_ID"
Write-Host "GOOGLE_CLOUD_LOCATION = $env:GOOGLE_CLOUD_LOCATION"
Write-Host "FIRESTORE_DATABASE = $env:FIRESTORE_DATABASE"

Write-Host "`nPlease set the following variables manually:" -ForegroundColor Red
Write-Host "BOT_TOKEN = your_telegram_bot_token"
Write-Host "GEMINI_API_KEY = your_gemini_api_key"

Write-Host "`nTo set them permanently, run:" -ForegroundColor Cyan
Write-Host "[Environment]::SetEnvironmentVariable('GOOGLE_APPLICATION_CREDENTIALS', '$env:GOOGLE_APPLICATION_CREDENTIALS', 'User')"
Write-Host "[Environment]::SetEnvironmentVariable('PROJECT_ID', '$env:PROJECT_ID', 'User')"
Write-Host "[Environment]::SetEnvironmentVariable('GOOGLE_CLOUD_LOCATION', '$env:GOOGLE_CLOUD_LOCATION', 'User')"
Write-Host "[Environment]::SetEnvironmentVariable('FIRESTORE_DATABASE', '$env:FIRESTORE_DATABASE', 'User')"

Write-Host "`nPress any key to continue..." -ForegroundColor Green
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
