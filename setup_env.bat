@echo off
echo Setting up environment variables for Bot Doc...

REM Set Google Cloud credentials
set GOOGLE_APPLICATION_CREDENTIALS=google-cloud-credentials.json
set PROJECT_ID=bot-doc-473208
set GOOGLE_CLOUD_LOCATION=asia-southeast1

REM Set Firestore database
set FIRESTORE_DATABASE=default

echo Environment variables set:
echo GOOGLE_APPLICATION_CREDENTIALS=%GOOGLE_APPLICATION_CREDENTIALS%
echo PROJECT_ID=%PROJECT_ID%
echo GOOGLE_CLOUD_LOCATION=%GOOGLE_CLOUD_LOCATION%
echo FIRESTORE_DATABASE=%FIRESTORE_DATABASE%

echo.
echo Please set the following variables manually:
echo BOT_TOKEN=your_telegram_bot_token
echo GEMINI_API_KEY=your_gemini_api_key

echo.
echo To set them permanently, run:
echo setx GOOGLE_APPLICATION_CREDENTIALS "%CD%\google-cloud-credentials.json"
echo setx PROJECT_ID "bot-doc-473208"
echo setx GOOGLE_CLOUD_LOCATION "asia-southeast1"
echo setx FIRESTORE_DATABASE "default"

pause
