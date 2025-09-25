# 🔧 Руководство по настройке Firestore

## ❌ Проблема
База данных Firestore не существует для проекта `bot-doc-473208`.

## ✅ Решение

### Шаг 1: Создание базы данных Firestore

1. **Перейдите по ссылке:** https://console.cloud.google.com/firestore?project=bot-doc-473208

2. **Выберите режим базы данных:**
   - Нажмите **"Создать базу данных"**
   - Выберите **"Native mode"** (рекомендуется)
   - Нажмите **"Далее"**

3. **Настройте расположение:**
   - Выберите регион: **"asia-southeast1"** (Сингапур)
   - Это соответствует настройкам в `env.local`
   - Нажмите **"Создать"**

4. **Дождитесь создания базы данных** (обычно 1-2 минуты)

### Шаг 2: Проверка настройки

После создания базы данных запустите проверку:

```bash
python setup_firestore.py
```

Должно появиться сообщение:
```
✅ Firestore клиент инициализирован успешно
✅ База данных Firestore доступна и работает
✅ Коллекция 'user_languages' готова к использованию
🎉 Firestore настроен успешно!
```

### Шаг 3: Запуск бота

После успешной настройки Firestore запустите бота:

```bash
python main_local.py
```

## 🔍 Альтернативные ссылки

Если основная ссылка не работает, попробуйте:

1. **Firestore Console:** https://console.cloud.google.com/firestore?project=bot-doc-473208
2. **Datastore Setup:** https://console.cloud.google.com/datastore/setup?project=bot-doc-473208
3. **Google Cloud Console:** https://console.cloud.google.com/?project=bot-doc-473208

## 📋 Требования

- ✅ Google Cloud проект: `bot-doc-473208`
- ✅ Service Account: `bot-doc-sa@bot-doc-473208.iam.gserviceaccount.com`
- ✅ Права доступа: Firestore Admin
- ✅ Регион: `asia-southeast1`

## 🚨 Если проблемы остаются

1. **Проверьте права доступа:**
   - Убедитесь, что Service Account имеет роль "Firestore Admin"
   - Перейдите в IAM & Admin → Service Accounts

2. **Проверьте API:**
   - Убедитесь, что Firestore API включен
   - Перейдите в APIs & Services → Library

3. **Проверьте квоты:**
   - Убедитесь, что не превышены лимиты проекта
