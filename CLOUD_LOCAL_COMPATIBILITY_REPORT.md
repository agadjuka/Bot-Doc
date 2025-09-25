# Отчет о различиях между локальной и облачной версиями

## Обзор

Проведено сравнение локальной версии (`main_local.py`) и облачной версии (`main.py`) с целью обеспечения **функциональной совместимости** при сохранении **архитектурных различий**, необходимых для разных сред развертывания.

## Ключевые различия (по дизайну)

### 1. Архитектурные различия

| Аспект | Локальная версия | Облачная версия |
|--------|------------------|-----------------|
| **Протокол** | Polling | Webhook (FastAPI) |
| **Запуск** | Синхронный `main()` | Асинхронный с FastAPI |
| **Переменные окружения** | `env.local` файл | Системные переменные Cloud Run |
| **Обработка ошибок** | `safe_start_bot()` с retry | Graceful degradation |
| **Keep-alive** | Не нужен | Обязателен для Cloud Run |
| **Мониторинг** | Консольные логи | FastAPI endpoints |

### 2. Функциональные требования

**Локальная версия должна:**
- Работать через polling
- Загружать настройки из `.env` файла
- Иметь retry логику для конфликтов
- Быть простой в отладке

**Облачная версия должна:**
- Работать через webhook
- Использовать системные переменные окружения
- Иметь keep-alive для Cloud Run
- Быть оптимизирована для production

## Внесенные изменения

### 1. Добавлено состояние `AWAITING_INPUT` в облачную версию

```python
states={
    config.AWAITING_INPUT: [
        MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_text),
        CommandHandler("help", message_handlers.help_command),
        CommandHandler("new_contract", document_handlers.new_contract_command)
    ],
    config.AWAITING_COMPANY_INFO: [
        MessageHandler(filters.TEXT & ~filters.COMMAND, document_handlers.handle_company_info),
        CommandHandler("cancel", document_handlers.cancel_document_creation)
    ],
},
```

### 2. Оптимизирована инициализация для Cloud Run

```python
async def initialize_bot():
    """Initialize the bot application and start background tasks for Cloud Run"""
    # Прямая инициализация без retry (Cloud Run сам перезапускает)
    # Keep-alive для предотвращения засыпания
    # Graceful degradation при ошибках
```

### 3. Добавлен endpoint статуса для мониторинга

```python
@app.get("/status")
async def cloud_status():
    """Статус облачной версии бота для Cloud Run"""
    # Проверка компонентов
    # Статус операционной готовности
    # Информация для мониторинга
```

## Результат

### ✅ Функциональная совместимость достигнута

Обе версии предоставляют **одинаковый пользовательский опыт**:

1. **ConversationHandler** с полным набором состояний
2. **Обработка команд** `/start`, `/help`, `/new_contract`
3. **Создание документов** через диалог
4. **Многоязычная поддержка** через LocaleManager
5. **AI обработка** через AIService

### 🔧 Архитектурные различия сохранены

**Локальная версия:**
- Polling для разработки
- `.env` файлы для конфигурации
- Retry логика для стабильности
- Простая отладка

**Облачная версия:**
- Webhook для production
- Системные переменные окружения
- Keep-alive для Cloud Run
- FastAPI endpoints для мониторинга

## Мониторинг облачной версии

Для проверки статуса используйте endpoint:

```bash
GET /status
```

Ответ содержит информацию о состоянии системы:

```json
{
  "version": "cloud",
  "environment": "Cloud Run",
  "protocol": "webhook",
  "components": {
    "application_initialized": true,
    "firestore_connected": true,
    "keep_alive_running": true,
    "locale_manager": true,
    "ai_service": true,
    "handlers": true
  },
  "status": "operational"
}
```

## Заключение

Облачная и локальная версии теперь **функционально идентичны** для пользователя, но **архитектурно оптимизированы** для своих сред развертывания. Это обеспечивает:

- **Единый пользовательский опыт** независимо от версии
- **Оптимальную производительность** в каждой среде
- **Простоту разработки** в локальной среде
- **Надежность работы** в production
