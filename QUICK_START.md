# Быстрый старт - Bot Doc

## ✅ Что уже настроено

1. **Google Cloud Credentials** - файл `google-cloud-credentials.json` скопирован и настроен
2. **Переменные окружения** - создан файл `env.local` с настройками
3. **Document Handler** - новый функционал для создания документов
4. **Локализация** - поддержка русского и английского языков

## 🚀 Запуск бота

### 1. Настройка переменных окружения

```cmd
# Запустите PowerShell скрипт для настройки
powershell -ExecutionPolicy Bypass -File setup_env.ps1
```

### 2. Активация Google Cloud APIs

**ВАЖНО**: Сначала активируйте необходимые API:

- **Firestore API**: https://console.developers.google.com/apis/api/firestore.googleapis.com/overview?project=bot-doc-473208
- **Gemini AI API**: https://console.developers.google.com/apis/api/generativelanguage.googleapis.com/overview?project=bot-doc-473208

### 3. Настройка токенов

Отредактируйте файл `env.local`:

```env
# Bot Configuration
BOT_TOKEN=ваш_токен_бота_здесь

# Gemini AI Configuration  
GEMINI_API_KEY=ваш_gemini_api_ключ_здесь
```

### 4. Запуск бота

```cmd
python main_local.py
```

## 📋 Новые команды

- `/start` - запуск бота
- `/help` - справка
- `/new_contract` - создание нового документа (новый функционал!)

## 🔧 Структура проекта

```
Bot-Doc/
├── handlers/
│   ├── document_handler.py      # Новый обработчик документов
│   ├── message_handlers.py      # Основные обработчики
│   └── callback_handlers.py     # Обработчики кнопок
├── config/
│   ├── locales/
│   │   ├── ru.py               # Русские тексты
│   │   └── en.py               # Английские тексты
│   └── settings.py             # Настройки бота
├── google-cloud-credentials.json  # Учетные данные Google
├── env.local                   # Переменные окружения
└── main_local.py              # Точка входа для локального запуска
```

## 🆕 Новый функционал - Document Handler

### Сценарий работы:

1. Пользователь отправляет `/new_contract`
2. Бот просит прислать карточку предприятия
3. Пользователь отправляет текст с информацией о компании
4. Бот подтверждает получение и сохраняет данные

### FSM States:

- `AWAITING_INPUT = 1` - основное состояние
- `AWAITING_COMPANY_INFO = 2` - ожидание информации о компании

## 🐛 Устранение проблем

### Ошибка "SERVICE_DISABLED"
- Активируйте Firestore API по ссылке выше

### Ошибка "GEMINI_API_KEY is required"
- Получите ключ в Google AI Studio и добавьте в `env.local`

### Ошибка "BOT_TOKEN не найден"
- Получите токен у @BotFather и добавьте в `env.local`

## 📚 Дополнительная документация

- `SETUP_GOOGLE_CREDENTIALS.md` - подробная настройка Google Cloud
- `ENABLE_APIS.md` - активация необходимых API
- `DOCUMENT_HANDLER_README.md` - документация по новому функционалу
