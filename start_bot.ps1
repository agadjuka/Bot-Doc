# Скрипт для запуска бота с правильными переменными окружения
Write-Host "🚀 Запуск AI Bot..." -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Cyan

# Устанавливаем переменные окружения
$env:GOOGLE_APPLICATION_CREDENTIALS = "D:\AI Nakladnie\Bot Doc\Bot-Doc\bot-doc-473208-706e6adceee1.json"
$env:FIRESTORE_DATABASE = "docbot"

Write-Host "✅ Переменные окружения установлены:" -ForegroundColor Green
Write-Host "   GOOGLE_APPLICATION_CREDENTIALS: $env:GOOGLE_APPLICATION_CREDENTIALS" -ForegroundColor Yellow
Write-Host "   FIRESTORE_DATABASE: $env:FIRESTORE_DATABASE" -ForegroundColor Yellow

Write-Host ""
Write-Host "🔧 Проверяем Firestore..." -ForegroundColor Cyan
python setup_firestore.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "🤖 Запускаем бота..." -ForegroundColor Green
    python main_local.py
} else {
    Write-Host "❌ Ошибка при проверке Firestore. Проверьте настройки." -ForegroundColor Red
    Write-Host "Нажмите любую клавишу для выхода..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
