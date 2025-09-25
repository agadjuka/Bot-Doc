# Настройка Google Cloud Credentials

## Что было сделано

1. ✅ Скопирован файл `bot-doc-473208-706e6adceee1.json` как `google-cloud-credentials.json`
2. ✅ Создан файл `env.local` с переменными окружения
3. ✅ Обновлен `main_local.py` для загрузки переменных из `env.local`
4. ✅ Созданы скрипты для настройки переменных окружения

## Настройка переменных окружения

### Вариант 1: Автоматическая настройка (PowerShell)

```powershell
# Запустите PowerShell от имени администратора
.\setup_env.ps1
```

### Вариант 2: Ручная настройка

Установите следующие переменные окружения:

```cmd
set GOOGLE_APPLICATION_CREDENTIALS=D:\AI Nakladnie\Bot Doc\Bot-Doc\google-cloud-credentials.json
set PROJECT_ID=bot-doc-473208
set GOOGLE_CLOUD_LOCATION=asia-southeast1
set FIRESTORE_DATABASE=default
```

### Вариант 3: Через env.local файл

Отредактируйте файл `env.local` и укажите ваши токены:

```env
# Bot Configuration
BOT_TOKEN=ваш_токен_бота_здесь

# Google Cloud Configuration (уже настроено)
GOOGLE_APPLICATION_CREDENTIALS=google-cloud-credentials.json
PROJECT_ID=bot-doc-473208
GOOGLE_CLOUD_LOCATION=asia-southeast1

# Gemini AI Configuration
GEMINI_API_KEY=ваш_gemini_api_ключ_здесь
```

## Проверка настройки

После настройки переменных окружения запустите бота:

```cmd
python main_local.py
```

## Информация о проекте

- **Project ID**: `bot-doc-473208`
- **Service Account**: `bot-doc-sa@bot-doc-473208.iam.gserviceaccount.com`
- **Credentials File**: `google-cloud-credentials.json`

## Необходимые API ключи

1. **BOT_TOKEN** - токен Telegram бота (получить у @BotFather)
2. **GEMINI_API_KEY** - ключ API для Gemini AI (получить в Google AI Studio)

## Устранение проблем

Если возникают ошибки:

1. Убедитесь, что файл `google-cloud-credentials.json` находится в папке `Bot-Doc`
2. Проверьте, что переменные окружения установлены правильно
3. Убедитесь, что у вас есть все необходимые API ключи
4. Проверьте, что проект `bot-doc-473208` активен в Google Cloud Console
