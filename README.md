# Telegram Bot Template

Базовый шаблон для создания Telegram ботов с поддержкой AI (Google Gemini) и деплоем в Google Cloud Run.

## 🚀 Быстрый старт

### Локальная разработка
```bash
# 1. Установка зависимостей
pip install -r requirements_local.txt

# 2. Создание .env файла
cp .env.example .env

# 3. Заполнение переменных окружения в .env
# BOT_TOKEN=your_telegram_bot_token
# GEMINI_API_KEY=your_gemini_api_key
# PROJECT_ID=your_google_cloud_project_id

# 4. Запуск локальной версии
python run_local.py
```

### Production деплой
```bash
# Автоматический деплой при push в main ветку
git push origin main
```

## 📁 Структура проекта

```
telegram-bot-template/
├── main.py                    # Production версия (FastAPI + webhook)
├── main_local.py             # Локальная версия (polling)
├── run_local.py              # Скрипт запуска локальной версии
├── requirements.txt          # Production зависимости
├── requirements_local.txt    # Локальные зависимости
├── env.example              # Пример конфигурации
├── .env                     # Ваши токены (создать вручную)
├── config/                  # Конфигурация
│   ├── settings.py         # Настройки бота
│   ├── secrets.py          # Управление секретами
│   ├── prompts.py          # AI промпты
│   └── locales/            # Локализация
│       ├── ru.py          # Русские тексты
│       ├── en.py          # Английские тексты
│       └── locale_manager.py  # Менеджер локализации
├── services/               # Сервисы
│   └── ai_service.py      # AI сервис (Google Gemini)
├── handlers/              # Обработчики
│   ├── message_handlers.py    # Обработчики сообщений
│   └── callback_handlers.py   # Обработчики callback'ов
├── utils/                 # Утилиты
│   └── message_sender.py  # Отправка сообщений
└── README.md             # Документация
```

## 🔧 Режимы работы

| Режим | Файл | Протокол | Назначение |
|-------|------|----------|------------|
| **Production** | `main.py` | Webhook (FastAPI) | Деплой в Google Cloud Run |
| **Local** | `main_local.py` | Polling | Локальная разработка |

## 🔐 Переменные окружения

### Обязательные
- `BOT_TOKEN` - Токен Telegram бота
- `GEMINI_API_KEY` - API ключ Google Gemini
- `PROJECT_ID` - ID проекта Google Cloud

### Опциональные
- `FIRESTORE_DATABASE` - Имя базы данных Firestore (по умолчанию: default)
- `SERVICE_URL` - URL сервиса для keep-alive (для Cloud Run)
- `GOOGLE_APPLICATION_CREDENTIALS` - Путь к файлу учетных данных Google Cloud
- `GOOGLE_APPLICATION_CREDENTIALS_JSON` - JSON учетных данных (для Cloud Run)

## 🛠️ Функциональность шаблона

- ✅ Базовые команды `/start` и `/help`
- ✅ Обработка текстовых сообщений с AI ответами
- ✅ Поддержка многоязычности (русский/английский)
- ✅ Интеграция с Google Gemini AI
- ✅ Firestore для хранения пользовательских данных
- ✅ Keep-alive для Cloud Run
- ✅ Логирование и обработка ошибок

## 📖 Использование

1. **Клонируйте репозиторий**
2. **Скопируйте `.env.example` в `.env`**
3. **Заполните необходимые переменные окружения**
4. **Установите зависимости**: `pip install -r requirements_local.txt`
5. **Запустите локально**: `python run_local.py`

## 🚀 Деплой в Google Cloud Run

1. **Настройте Google Cloud проект**
2. **Включите необходимые API** (Cloud Run, Firestore)
3. **Создайте service account** с нужными правами
4. **Настройте переменные окружения** в Cloud Run
5. **Деплойте**: `gcloud run deploy`

## 🔧 Кастомизация

### Добавление новых команд
1. Добавьте обработчик в `handlers/message_handlers.py`
2. Зарегистрируйте команду в `main.py` или `main_local.py`

### Добавление новых языков
1. Создайте файл в `config/locales/` (например, `de.py`)
2. Добавьте переводы в формате `LANG_TRANSLATIONS`
3. Обновите `locale_manager.py`

### Изменение AI поведения
1. Отредактируйте промпты в `config/prompts.py`
2. Настройте AI сервис в `services/ai_service.py`

## 📝 Лицензия

MIT License - используйте свободно для своих проектов.