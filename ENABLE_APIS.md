# Активация Google Cloud APIs

## Необходимые API для работы бота

### 1. Cloud Firestore API
**Статус**: ❌ Не активирован  
**Ссылка**: https://console.developers.google.com/apis/api/firestore.googleapis.com/overview?project=bot-doc-473208

### 2. Gemini AI API (если используется)
**Статус**: ⚠️ Требует проверки  
**Ссылка**: https://console.developers.google.com/apis/api/generativelanguage.googleapis.com/overview?project=bot-doc-473208

## Пошаговая инструкция

### Шаг 1: Активация Firestore API

1. Перейдите по ссылке: https://console.developers.google.com/apis/api/firestore.googleapis.com/overview?project=bot-doc-473208
2. Нажмите кнопку "Enable" (Включить)
3. Дождитесь активации (может занять несколько минут)

### Шаг 2: Проверка активации

После активации запустите тест:

```cmd
python test_google_connection.py
```

### Шаг 3: Создание Firestore базы данных

1. Перейдите в Firestore Console: https://console.firebase.google.com/project/bot-doc-473208/firestore
2. Создайте базу данных в режиме "Native mode"
3. Выберите регион (рекомендуется: asia-southeast1)

## Альтернативный способ активации через gcloud CLI

Если у вас установлен gcloud CLI:

```bash
gcloud services enable firestore.googleapis.com --project=bot-doc-473208
gcloud services enable generativelanguage.googleapis.com --project=bot-doc-473208
```

## Проверка статуса API

```bash
gcloud services list --enabled --project=bot-doc-473208
```

## Устранение проблем

- **403 SERVICE_DISABLED**: API не активирован - следуйте инструкции выше
- **403 PERMISSION_DENIED**: Недостаточно прав - убедитесь, что используете правильный service account
- **404 NOT_FOUND**: Проект не найден - проверьте PROJECT_ID

## После активации

После успешной активации API бот должен работать корректно с:
- ✅ Firestore для хранения языковых настроек
- ✅ Gemini AI для обработки сообщений
- ✅ Google Cloud для всех сервисов
