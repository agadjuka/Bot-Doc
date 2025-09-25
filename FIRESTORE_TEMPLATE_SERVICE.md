# Firestore Template Service Documentation

## Обзор

`FirestoreService` - это сервис для управления пользовательскими шаблонами документов в Firestore. Он предоставляет асинхронные методы для добавления, получения, обновления и удаления шаблонов документов.

## Структура данных

### Коллекция `users`
- **ID документа**: `telegram_user_id` (строка)
- **Поля**:
  - `role`: роль пользователя ("admin" или "user")
  - `created_at`: дата создания пользователя
  - `display_mode`: режим отображения ("desktop" или "mobile")

### Под-коллекция `document_templates`
- **Путь**: `users/{user_id}/document_templates/{template_doc_id}`
- **Поля**:
  - `template_name`: название шаблона (строка)
  - `file_id`: ID файла в Telegram (строка)
  - `file_type`: тип файла (строка, по умолчанию 'docx')
  - `created_at`: дата создания шаблона (timestamp)
  - `updated_at`: дата последнего обновления (timestamp, опционально)

## API Методы

### `add_template(user_id, template_name, file_id, file_type='docx')`
Добавляет новый шаблон документа в коллекцию пользователя.

**Параметры:**
- `user_id` (int): ID пользователя Telegram
- `template_name` (str): Название шаблона
- `file_id` (str): ID файла в Telegram
- `file_type` (str): Тип файла (по умолчанию 'docx')

**Возвращает:** `bool` - True если успешно, False в противном случае

**Пример:**
```python
success = await firestore_service.add_template(
    user_id=123456789,
    template_name="Договор поставки",
    file_id="BAADBAADrwADBREAAYag8gABhqDyAAE",
    file_type="docx"
)
```

### `get_templates(user_id)`
Получает все шаблоны пользователя.

**Параметры:**
- `user_id` (int): ID пользователя Telegram

**Возвращает:** `List[Dict[str, Any]]` - Список словарей с информацией о шаблонах

**Пример:**
```python
templates = await firestore_service.get_templates(123456789)
for template in templates:
    print(f"Название: {template['template_name']}")
    print(f"ID документа: {template['template_doc_id']}")
    print(f"ID файла: {template['file_id']}")
```

### `get_template_file_id(user_id, template_doc_id)`
Получает file_id конкретного шаблона по его ID в Firestore.

**Параметры:**
- `user_id` (int): ID пользователя Telegram
- `template_doc_id` (str): ID документа шаблона в Firestore

**Возвращает:** `Optional[str]` - file_id если найден, None в противном случае

**Пример:**
```python
file_id = await firestore_service.get_template_file_id(
    user_id=123456789,
    template_doc_id="abc123def456"
)
```

### `delete_template(user_id, template_doc_id)`
Удаляет шаблон из коллекции пользователя.

**Параметры:**
- `user_id` (int): ID пользователя Telegram
- `template_doc_id` (str): ID документа шаблона в Firestore

**Возвращает:** `bool` - True если успешно, False в противном случае

### `update_template_name(user_id, template_doc_id, new_name)`
Обновляет название шаблона.

**Параметры:**
- `user_id` (int): ID пользователя Telegram
- `template_doc_id` (str): ID документа шаблона в Firestore
- `new_name` (str): Новое название шаблона

**Возвращает:** `bool` - True если успешно, False в противном случае

### `get_template_info(user_id, template_doc_id)`
Получает полную информацию о шаблоне.

**Параметры:**
- `user_id` (int): ID пользователя Telegram
- `template_doc_id` (str): ID документа шаблона в Firestore

**Возвращает:** `Optional[Dict[str, Any]]` - Словарь с информацией о шаблоне или None

## Инициализация

### Глобальный экземпляр
```python
from services.firestore_service import get_firestore_service

# Получить глобальный экземпляр (использует db из main.py)
firestore_service = get_firestore_service()

# Или передать собственный экземпляр Firestore
firestore_service = get_firestore_service(db_instance=my_db)
```

### Прямое создание
```python
from services.firestore_service import FirestoreService
from google.cloud import firestore

db = firestore.Client()
firestore_service = FirestoreService(db)
```

## Обработка ошибок

Все методы возвращают `False` или `None` в случае ошибки и выводят сообщения об ошибках в консоль. Рекомендуется проверять возвращаемые значения:

```python
success = await firestore_service.add_template(user_id, name, file_id)
if not success:
    print("Не удалось добавить шаблон")
    return
```

## Тестирование

Для тестирования сервиса используйте скрипт `test_firestore_service.py`:

```bash
python test_firestore_service.py
```

Убедитесь, что установлены переменные окружения для доступа к Firestore:
- `GOOGLE_APPLICATION_CREDENTIALS` - путь к файлу ключей
- или `GOOGLE_APPLICATION_CREDENTIALS_JSON` - JSON ключи в переменной окружения

## Интеграция с ботом

Сервис готов к интеграции с Telegram ботом. Пример использования в обработчике сообщений:

```python
from services.firestore_service import get_firestore_service

async def handle_document_upload(update, context):
    user_id = update.effective_user.id
    document = update.message.document
    
    if document.mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        # Сохраняем шаблон
        firestore_service = get_firestore_service()
        success = await firestore_service.add_template(
            user_id=user_id,
            template_name=document.file_name,
            file_id=document.file_id
        )
        
        if success:
            await update.message.reply_text("✅ Шаблон успешно сохранен!")
        else:
            await update.message.reply_text("❌ Ошибка при сохранении шаблона")
```

## Безопасность

- Все операции проверяют существование пользователя
- Автоматически создается документ пользователя при первом добавлении шаблона
- Валидация входных параметров
- Обработка ошибок без прерывания работы приложения
