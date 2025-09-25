# Быстрый старт: Управление шаблонами документов

## Что реализовано

✅ **FirestoreService** - сервис для работы с шаблонами в Firestore
✅ **Структура данных** - коллекция `users` с под-коллекцией `document_templates`
✅ **API методы** - добавление, получение, обновление и удаление шаблонов
✅ **Интеграция** - готовые примеры для Telegram бота
✅ **Тестирование** - тестовый скрипт для проверки функциональности

## Структура данных в Firestore

```
users/
├── {telegram_user_id}/
│   ├── role: "user" | "admin"
│   ├── created_at: timestamp
│   ├── display_mode: "desktop" | "mobile"
│   └── document_templates/ (под-коллекция)
│       ├── {template_doc_id}/
│       │   ├── template_name: string
│       │   ├── file_id: string (Telegram file ID)
│       │   ├── file_type: "docx"
│       │   └── created_at: timestamp
│       └── ...
```

## Быстрый тест

1. **Запустите тест:**
   ```bash
   cd Bot-Doc
   python test_firestore_service.py
   ```

2. **Проверьте подключение к Firestore:**
   - Убедитесь, что установлены переменные окружения для Google Cloud
   - Или используйте `GOOGLE_APPLICATION_CREDENTIALS_JSON`

## Использование в коде

### Базовое использование
```python
from services.firestore_service import get_firestore_service

# Получить сервис
firestore_service = get_firestore_service()

# Добавить шаблон
success = await firestore_service.add_template(
    user_id=123456789,
    template_name="Договор поставки",
    file_id="BAADBAADrwADBREAAYag8gABhqDyAAE"
)

# Получить все шаблоны пользователя
templates = await firestore_service.get_templates(123456789)

# Получить file_id конкретного шаблона
file_id = await firestore_service.get_template_file_id(
    user_id=123456789,
    template_doc_id="abc123def456"
)
```

### Интеграция с Telegram ботом
```python
from template_integration_example import TemplateManager

# Создать менеджер шаблонов
template_manager = TemplateManager()

# В обработчике загрузки документа
await template_manager.handle_document_upload(update, context)

# В обработчике команды /templates
await template_manager.list_user_templates(update, context)
```

## API Методы

| Метод | Описание | Параметры | Возвращает |
|-------|----------|-----------|------------|
| `add_template()` | Добавить шаблон | user_id, template_name, file_id, file_type | bool |
| `get_templates()` | Получить все шаблоны | user_id | List[Dict] |
| `get_template_file_id()` | Получить file_id шаблона | user_id, template_doc_id | str \| None |
| `delete_template()` | Удалить шаблон | user_id, template_doc_id | bool |
| `update_template_name()` | Переименовать шаблон | user_id, template_doc_id, new_name | bool |
| `get_template_info()` | Получить полную информацию | user_id, template_doc_id | Dict \| None |

## Следующие шаги

1. **Интеграция с ботом** - добавьте обработчики команд из `template_integration_example.py`
2. **Обработка документов** - реализуйте логику создания документов на основе шаблонов
3. **UI улучшения** - добавьте inline клавиатуры для удобного выбора шаблонов
4. **Валидация** - добавьте проверку формата и размера загружаемых файлов

## Файлы проекта

- `services/firestore_service.py` - основной сервис
- `test_firestore_service.py` - тестовый скрипт
- `template_integration_example.py` - примеры интеграции
- `FIRESTORE_TEMPLATE_SERVICE.md` - полная документация
- `TEMPLATE_QUICK_START.md` - это руководство

## Требования

- Python 3.8+
- google-cloud-firestore
- python-telegram-bot (для интеграции с ботом)
- Настроенные учетные данные Google Cloud

## Поддержка

При возникновении проблем:
1. Проверьте подключение к Firestore
2. Убедитесь в правильности переменных окружения
3. Запустите тестовый скрипт для диагностики
4. Проверьте логи в консоли
