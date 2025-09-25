# 🚀 Руководство по настройке AI Bot

Полное руководство по настройке локальной разработки и production деплоя.

## 📋 Что было создано

### Локальная разработка
- `main_local.py` - Локальная версия бота (polling)
- `run_local.py` - Скрипт запуска локальной версии
- `requirements_local.txt` - Зависимости для локальной разработки
- `dev_setup.py` - Автоматическая настройка среды разработки
- `env.example` - Пример конфигурации

### Production деплой
- `main.py` - Production версия (FastAPI + webhook)
- `requirements.txt` - Production зависимости
- `.github/workflows/deploy.yml` - GitHub Actions для автоматического деплоя
- `Dockerfile` - Docker контейнер для Cloud Run
- `cloudbuild.yaml` - Google Cloud Build конфигурация

### Утилиты
- `start.py` - Универсальный скрипт запуска
- `switch_mode.py` - Переключение между версиями
- `README_LOCAL.md` - Документация по локальной разработке

## 🏁 Быстрый старт

### 1. Настройка локальной среды

```bash
# Клонируйте репозиторий (если еще не сделано)
git clone <your-repo-url>
cd "AI Bot"

# Автоматическая настройка
python dev_setup.py

# Отредактируйте .env файл с вашими токенами
# BOT_TOKEN=your_telegram_bot_token
# POSTER_TOKEN=your_poster_api_token
# PROJECT_ID=your_google_cloud_project_id

# Запуск локальной версии
python start.py
```

### 2. Настройка production деплоя

1. **Настройте GitHub Secrets:**
   - `BOT_TOKEN` - Токен Telegram бота
   - `PROJECT_ID` - ID проекта Google Cloud
   - `GCP_SA_KEY` - JSON ключ сервисного аккаунта

2. **Деплой происходит автоматически при push в main ветку**

## 🔧 Режимы работы

### Локальная разработка
```bash
# Автоматический выбор режима
python start.py

# Принудительно локальный режим
python start.py local

# Прямой запуск
python run_local.py
```

### Production
```bash
# Принудительно production режим
python start.py production

# Прямой запуск
python main.py
```

## 📁 Структура файлов

```
AI Bot/
├── main.py                    # Production версия (FastAPI + webhook)
├── main_local.py             # Локальная версия (polling)
├── start.py                  # Универсальный запуск
├── run_local.py              # Запуск локальной версии
├── dev_setup.py              # Настройка среды разработки
├── switch_mode.py            # Переключение между версиями
├── requirements.txt          # Production зависимости
├── requirements_local.txt    # Локальные зависимости
├── env.example              # Пример конфигурации
├── .env                     # Ваши токены (создать вручную)
├── .github/workflows/       # GitHub Actions
│   └── deploy.yml
├── config/                  # Конфигурация
├── services/               # Сервисы
├── handlers/               # Обработчики
├── utils/                  # Утилиты
├── models/                 # Модели данных
├── validators/             # Валидация
├── README.md              # Основная документация
├── README_LOCAL.md        # Локальная разработка
└── SETUP_GUIDE.md         # Это руководство
```

## 🛠️ Команды разработки

### Основные команды
```bash
# Универсальный запуск
python start.py

# Настройка среды
python dev_setup.py

# Переключение режимов
python switch_mode.py local    # Локальный режим
python switch_mode.py prod     # Production режим
python switch_mode.py status   # Статус

# Прямой запуск
python run_local.py           # Локальная версия
python main.py                # Production версия
```

### Git команды
```bash
# Коммит изменений
git add .
git commit -m "Описание изменений"

# Деплой в production
git push origin main
```

## 🔍 Troubleshooting

### Локальная разработка

**Ошибка: "BOT_TOKEN не найден"**
```bash
# Проверьте файл .env
cat .env

# Пересоздайте .env
python dev_setup.py
```

**Ошибка: "Конфликт обнаружен"**
- Остановите другие экземпляры бота
- Подождите несколько секунд
- Попробуйте снова

**Ошибка импорта модулей**
```bash
# Переустановите зависимости
pip install -r requirements_local.txt
```

### Production деплой

**Деплой не запускается**
- Проверьте GitHub Secrets
- Убедитесь, что push в main ветку
- Проверьте логи в GitHub Actions

**Бот не отвечает в production**
- Проверьте логи Cloud Run
- Убедитесь, что webhook настроен правильно
- Проверьте переменные окружения

## 📚 Дополнительная документация

- **[README.md](README.md)** - Основная документация
- **[README_LOCAL.md](README_LOCAL.md)** - Локальная разработка
- **[GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md)** - Настройка Google Sheets

## 🎯 Workflow разработки

1. **Локальная разработка:**
   ```bash
   python dev_setup.py      # Настройка
   python start.py          # Запуск
   # Редактируйте код
   # Тестируйте изменения
   ```

2. **Коммит и деплой:**
   ```bash
   git add .
   git commit -m "Описание изменений"
   git push origin main     # Автоматический деплой
   ```

3. **Проверка production:**
   - Проверьте GitHub Actions
   - Проверьте Cloud Run
   - Протестируйте бота

## ✅ Готово!

Теперь у вас есть:
- ✅ Локальная версия для разработки
- ✅ Production версия для деплоя
- ✅ Автоматический деплой в Google Cloud Run
- ✅ Удобные скрипты для работы
- ✅ Полная документация

**Начните с:** `python dev_setup.py`
