# Document Handler - Новый функционал

## Описание

Реализован новый диалог с использованием машины состояний (FSM) для создания документов на основе карточки предприятия.

## Реализованные компоненты

### 1. Новый обработчик `handlers/document_handler.py`

- **Класс**: `DocumentHandler`
- **Наследование**: `BaseMessageHandler`
- **Функциональность**:
  - Обработка команды `/new_contract`
  - Обработка ввода информации о компании
  - Отмена создания документа
  - Локализованные сообщения

### 2. Новые состояния FSM

- **`AWAITING_COMPANY_INFO = 2`** - ожидание информации о компании

### 3. Локализованные тексты

#### Русский язык (`config/locales/ru.py`)
```python
"document": {
    "new_contract_start": "📄 **Создание нового документа.**\n\nПожалуйста, скопируйте и пришлите мне реквизиты компании (карточку предприятия) одним сообщением. Я проанализирую их и подготовлю документ.",
    "info_received": "✅ Информация принята. Начинаю обработку...",
    "creation_cancelled": "❌ Создание документа отменено.",
}
```

#### Английский язык (`config/locales/en.py`)
```python
"document": {
    "new_contract_start": "📄 **Creating new document.**\n\nPlease copy and send me the company details (company card) in one message. I will analyze them and prepare the document.",
    "info_received": "✅ Information received. Starting processing...",
    "creation_cancelled": "❌ Document creation cancelled.",
}
```

### 4. Интеграция с основными файлами

- **`main.py`** - добавлен импорт и регистрация DocumentHandler
- **`main_local.py`** - добавлен импорт и регистрация DocumentHandler
- **`config/settings.py`** - добавлено новое состояние AWAITING_COMPANY_INFO

## Использование

### Команды бота

1. **`/new_contract`** - начать создание нового документа
2. **`/cancel`** - отменить текущую операцию

### Сценарий работы

1. Пользователь отправляет команду `/new_contract`
2. Бот переводит пользователя в состояние `AWAITING_COMPANY_INFO`
3. Бот отправляет сообщение с просьбой прислать карточку предприятия
4. Пользователь отправляет текст с информацией о компании
5. Бот подтверждает получение информации и завершает FSM
6. Информация сохраняется в `context.user_data['company_info']`

### Обработка ошибок

- Поддержка отмены на любом этапе через команду `/cancel`
- Локализованные сообщения об ошибках
- Graceful fallback к основному состоянию

## Технические детали

### FSM States
```python
states = {
    config.AWAITING_COMPANY_INFO: [
        MessageHandler(filters.TEXT & ~filters.COMMAND, document_handlers.handle_company_info),
        CommandHandler("cancel", document_handlers.cancel_document_creation)
    ],
}
```

### Entry Points
```python
entry_points = [
    CommandHandler("start", message_handlers.start),
    CommandHandler("help", message_handlers.help_command),
    CommandHandler("new_contract", document_handlers.new_contract_command),
    MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_text)
]
```

## Расширение функциональности

Для добавления дополнительных этапов обработки документа:

1. Добавить новые состояния в `config/settings.py`
2. Создать новые методы в `DocumentHandler`
3. Обновить `states` в ConversationHandler
4. Добавить локализованные тексты

## Тестирование

Все компоненты протестированы и готовы к использованию:
- ✅ Импорт модулей
- ✅ Локализация
- ✅ Конфигурация
- ✅ Интеграция с основными файлами
