# Архитектура системы управления шаблонами

## Общая схема

```
┌─────────────────────────────────────────────────────────────────┐
│                    TELEGRAM BOT                                │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │ Message Handlers│    │ Document Handler│    │ Command      │ │
│  │                 │    │                 │    │ Handlers     │ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SERVICES LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │ FirestoreService│    │ UserService     │    │ AIService    │ │
│  │                 │    │                 │    │              │ │
│  │ • add_template()│    │ • get_user_role │    │ • AI models  │ │
│  │ • get_templates │    │ • set_user_role │    │ • Analysis   │ │
│  │ • delete_template│   │ • whitelist     │    │              │ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FIRESTORE DATABASE                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │ users/          │    │ document_templates/                  │ │
│  │                 │    │ (subcollection) │    │              │ │
│  │ • user_id       │    │ • template_name │    │              │ │
│  │ • role          │    │ • file_id       │    │              │ │
│  │ • display_mode  │    │ • file_type     │    │              │ │
│  │ • created_at    │    │ • created_at    │    │              │ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Поток данных

### 1. Загрузка шаблона
```
User uploads .docx file
        │
        ▼
Telegram Bot receives document
        │
        ▼
Document Handler processes file
        │
        ▼
FirestoreService.add_template()
        │
        ▼
Firestore: users/{user_id}/document_templates/{doc_id}
```

### 2. Получение списка шаблонов
```
User sends /templates command
        │
        ▼
Command Handler processes command
        │
        ▼
FirestoreService.get_templates()
        │
        ▼
Firestore: Query document_templates subcollection
        │
        ▼
Return formatted list to user
```

### 3. Использование шаблона
```
User sends /use_template {template_id}
        │
        ▼
Command Handler processes command
        │
        ▼
FirestoreService.get_template_file_id()
        │
        ▼
Firestore: Get specific template document
        │
        ▼
Return file_id for document generation
```

## Структура файлов

```
Bot-Doc/
├── services/
│   ├── firestore_service.py      # Основной сервис для шаблонов
│   ├── user_service.py           # Управление пользователями
│   └── ai_service.py             # AI функциональность
├── handlers/
│   ├── message_handlers.py       # Обработчики сообщений
│   ├── document_handler.py       # Обработка документов
│   └── callback_handlers.py      # Обработчики callback'ов
├── config/
│   ├── settings.py               # Настройки бота
│   └── prompts.py                # Промпты для AI
├── test_firestore_service.py     # Тестирование сервиса
├── template_integration_example.py # Примеры интеграции
└── main.py                       # Главный файл приложения
```

## Компоненты системы

### FirestoreService
- **Назначение**: Управление шаблонами документов в Firestore
- **Основные методы**:
  - `add_template()` - добавление шаблона
  - `get_templates()` - получение всех шаблонов пользователя
  - `get_template_file_id()` - получение file_id конкретного шаблона
  - `delete_template()` - удаление шаблона
  - `update_template_name()` - переименование шаблона

### Структура данных Firestore
- **Коллекция `users`**: Основная информация о пользователях
- **Под-коллекция `document_templates`**: Шаблоны документов пользователя
- **Поля шаблона**:
  - `template_name` - название шаблона
  - `file_id` - ID файла в Telegram
  - `file_type` - тип файла (docx)
  - `created_at` - дата создания

### Интеграция с ботом
- **Обработчики команд**: `/templates`, `/use_template`, `/delete_template`
- **Обработчики документов**: Автоматическое сохранение .docx файлов как шаблонов
- **Валидация**: Проверка типа файла и размера

## Безопасность

- **Проверка пользователей**: Все операции привязаны к telegram_user_id
- **Валидация данных**: Проверка входных параметров
- **Обработка ошибок**: Graceful handling без прерывания работы
- **Изоляция данных**: Каждый пользователь видит только свои шаблоны

## Масштабируемость

- **Асинхронные операции**: Все методы используют async/await
- **Кэширование**: Возможность добавления кэша для часто используемых данных
- **Пагинация**: Готовность к добавлению пагинации для больших списков
- **Индексы**: Firestore автоматически создает индексы для запросов
