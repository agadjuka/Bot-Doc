# Единая система языка для AI Bot

## 🎯 Проблема, которую решает

Ранее в боте была проблема с несогласованностью языков:
- При перезагрузке бота первые сообщения приходили на русском
- После нажатия кнопок язык переключался на сохраненный в Firestore
- Требовалось вручную прописывать загрузку языка в каждом обработчике

## ✅ Решение

Создана единая система, которая автоматически загружает язык из Firestore для всех операций без необходимости дополнительного кода.

## 🏗️ Архитектура

### Основные компоненты

1. **`LocaleManager`** - центральный менеджер языка
2. **`LanguageService`** - работа с Firestore
3. **`BaseMessageHandler`** и **`BaseCallbackHandler`** - базовые обработчики
4. **Файлы переводов** - `ru.py`, `en.py`, `id.py`

### Принцип работы

```
Любой вызов get_text() → LocaleManager.get_text() → 
→ Проверка context.user_data['language'] → 
→ Если нет, загрузка из Firestore → 
→ Сохранение в context → 
→ Возврат переведенного текста
```

## 🔧 Изменения в коде

### 1. LocaleManager (config/locales/locale_manager.py)

**Улучшен метод `get_language_from_context`:**
- Добавлено логирование для отладки
- Автоматическая загрузка из Firestore
- Сохранение в контекст для кэширования

**Упрощен метод `get_text`:**
- Теперь автоматически загружает язык из Firestore
- Убрана необходимость в `get_text_with_auto_load`

### 2. Базовые обработчики

**BaseMessageHandler и BaseCallbackHandler:**
- `get_text()` теперь принимает `update` параметр
- `get_text_with_auto_load()` стал алиасом для `get_text()`
- Все методы (`get_button_text`, `get_emoji`) обновлены

### 3. Основные обработчики

**MessageHandlers и CallbackHandlers:**
- Все вызовы `get_text_with_auto_load()` заменены на `get_text()`
- Добавлен параметр `update=update` во все вызовы
- Убраны ручные вызовы `ensure_language_loaded()`
- Используется `locale_manager.get_language_from_context()` для определения языка

## 📋 Как использовать

### Для разработчиков

**Простой способ (рекомендуется):**
```python
# В любом обработчике
text = self.get_text("welcome.start_message", context, update=update, user="UserName")
```

**С явным указанием языка:**
```python
text = self.get_text("welcome.start_message", context, language="en", user="UserName")
```

### Приоритет определения языка

1. **Явно указанный язык** (`language` параметр)
2. **Язык в контексте** (`context.user_data['language']`)
3. **Язык из Firestore** (автоматическая загрузка)
4. **Язык по умолчанию** (русский)

## 🚀 Преимущества

### ✅ Автоматизация
- Не нужно помнить о загрузке языка
- Один вызов `get_text()` решает все
- Работает во всех обработчиках

### ✅ Согласованность
- Все сообщения на одном языке
- Нет переключений языка в процессе работы
- Единообразное поведение

### ✅ Простота разработки
- Новые обработчики автоматически поддерживают языки
- Не нужно прописывать `ensure_language_loaded()`
- Меньше кода, меньше ошибок

### ✅ Производительность
- Кэширование языка в контексте
- Один запрос к Firestore на сессию
- Быстрая работа

## 🧪 Тестирование

Создан тестовый скрипт `test_unified_language_system.py`:

```bash
python test_unified_language_system.py
```

Тесты проверяют:
- Язык в контексте
- Загрузку из Firestore
- Fallback на русский
- Интерполяцию переменных

## 📝 Примеры использования

### В обработчике сообщений
```python
async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Автоматически загрузит язык из Firestore
    text = self.get_text("welcome.start_message", context, update=update, 
                        user=update.effective_user.mention_html())
    await update.message.reply_html(text)
```

### В обработчике callback'ов
```python
async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Автоматически загрузит язык из Firestore
    button_text = self.get_button_text("buttons.analyze_receipt", context, update=update)
    keyboard = [[InlineKeyboardButton(button_text, callback_data="analyze_receipt")]]
```

### С интерполяцией переменных
```python
# Переменные автоматически подставляются
text = self.get_text("status.line_deleted", context, update=update, 
                    line_number=5, user="UserName")
```

## 🔍 Отладка

Система выводит отладочные сообщения:
```
DEBUG: Loading language from Firestore for user 12345
DEBUG: Retrieved language from Firestore: 'en'
DEBUG: Language 'en' saved to context for user 12345
```

## 🔧 Исправления

### Проблема: Первые сообщения на неправильном языке

**Причина:** Ручной вызов `ensure_language_loaded()` не гарантировал загрузку языка до показа сообщений.

**Решение:** 
1. Убраны ручные вызовы `ensure_language_loaded()`
2. Используется `locale_manager.get_language_from_context()` для определения языка
3. Все вызовы `get_text()` автоматически загружают язык из Firestore

### Код до исправления:
```python
# Проблемный код
self.ensure_language_loaded(update, context)
current_language = context.user_data.get('language', self.locale_manager.DEFAULT_LANGUAGE)
```

### Код после исправления:
```python
# Исправленный код
current_language = self.locale_manager.get_language_from_context(context, update)
```

## 🎉 Результат

Теперь бот работает согласованно:
- ✅ Все сообщения на выбранном языке с самого начала
- ✅ Нет переключений языка
- ✅ Простое добавление новых функций
- ✅ Автоматическая работа с Firestore
- ✅ Исправлена проблема с первыми сообщениями
