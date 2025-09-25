# Инструкция по запуску бота

## ✅ Что уже настроено

1. **Google Cloud Credentials** - файл `google-cloud-credentials.json` готов
2. **Переменные окружения** - все Google Cloud переменные настроены
3. **Firestore** - подключение работает
4. **Gemini AI** - инициализация работает

## 🚀 Запуск бота

### Вариант 1: Быстрый запуск (PowerShell)

```powershell
# Установите токены
$env:BOT_TOKEN = "ваш_реальный_токен_бота"
$env:GEMINI_API_KEY = "ваш_реальный_gemini_ключ"

# Запустите бота
python main_local.py
```

### Вариант 2: Через скрипт

```powershell
# Установите токены
$env:BOT_TOKEN = "ваш_реальный_токен_бота"
$env:GEMINI_API_KEY = "ваш_реальный_gemini_ключ"

# Запустите через скрипт
python run_bot.py
```

## 🔑 Где получить токены

### BOT_TOKEN (Telegram Bot)
1. Напишите @BotFather в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте полученный токен

### GEMINI_API_KEY (Google AI)
1. Перейдите на https://aistudio.google.com/
2. Войдите в аккаунт Google
3. Создайте новый API ключ
4. Скопируйте ключ

## ✅ Проверка работы

После запуска вы должны увидеть:
```
✅ Firestore клиент инициализирован успешно
✅ Gemini AI инициализирован с моделью: gemini-2.5-flash
✅ Language service initialized
✅ Global LocaleManager initialized
🚀 Бот запускается...
```

## 🆕 Новые команды

- `/start` - запуск бота
- `/help` - справка  
- `/new_contract` - создание нового документа

## 🐛 Устранение проблем

### "The token was rejected by the server"
- Проверьте правильность BOT_TOKEN
- Убедитесь, что токен не содержит лишних пробелов

### "GEMINI_API_KEY is required"
- Установите переменную: `$env:GEMINI_API_KEY = "ваш_ключ"`

### "Firestore API has not been used"
- Активируйте Firestore API: https://console.developers.google.com/apis/api/firestore.googleapis.com/overview?project=bot-doc-473208
