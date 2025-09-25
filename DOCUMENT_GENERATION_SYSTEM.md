# Система генерации документов

## Обзор

Полная система для автоматического создания документов Word на основе реквизитов компании, извлеченных с помощью Gemini AI.

## Компоненты системы

### 1. DocumentParserService (`services/document_parser_service.py`)

**Назначение:** Анализ текста с реквизитами компании с помощью Gemini AI

**Основные методы:**
- `parse_company_info(text: str) -> dict` - извлекает структурированные данные из текста

**Извлекаемые поля:**
- `COMPANY_FULL_NAME` - полное наименование компании
- `COMPANY_SHORT_NAME` - краткое наименование
- `INN` - ИНН
- `KPP` - КПП
- `OGRN` - ОГРН
- `LEGAL_ADDRESS` - юридический адрес
- `DIRECTOR_FULL_NAME` - ФИО директора
- `DIRECTOR_POSITION` - должность директора

### 2. DocumentGeneratorService (`services/document_generator_service.py`)

**Назначение:** Генерация .docx документов из шаблонов

**Основные методы:**
- `fill_document(template_path: str, data: dict) -> bytes` - заполняет шаблон данными
- `get_template_path(template_name: str) -> str` - получает путь к шаблону
- `create_sample_template(template_name: str) -> str` - создает тестовый шаблон

### 3. DocumentHandler (`handlers/document_handler.py`)

**Назначение:** Интеграция всех сервисов в Telegram бота

**Основные методы:**
- `new_contract_command()` - запуск процесса создания документа
- `handle_company_info()` - обработка введенных реквизитов

## Использование

### В Telegram боте

1. Пользователь отправляет команду `/new_contract`
2. Бот запрашивает реквизиты компании
3. Пользователь отправляет текст с реквизитами
4. Бот анализирует текст с помощью Gemini AI
5. Бот создает документ Word и отправляет его пользователю

### Программное использование

```python
from services.document_parser_service import DocumentParserService
from services.document_generator_service import DocumentGeneratorService

# Парсинг реквизитов
parser = DocumentParserService()
data = await parser.parse_company_info("текст с реквизитами")

# Генерация документа
generator = DocumentGeneratorService()
document_bytes = generator.fill_document("templates/template_test.docx", data)
```

## Шаблоны документов

### Расположение
Шаблоны хранятся в папке `templates/`

### Формат плейсхолдеров
В шаблонах используются плейсхолдеры в формате `{{FIELD_NAME}}`:
- `{{COMPANY_FULL_NAME}}`
- `{{INN}}`
- `{{LEGAL_ADDRESS}}`
- и т.д.

### Создание нового шаблона
1. Создайте .docx файл в папке `templates/`
2. Вставьте плейсхолдеры в нужные места
3. Используйте точные названия полей из DocumentParserService

## Тестирование

Запустите тестовый скрипт:
```bash
python test_document_system.py
```

## Требования

### Зависимости
- `docxtpl==0.20.1` - для работы с шаблонами Word
- `python-docx==1.2.0` - для создания шаблонов
- `google-generativeai==0.8.3` - для работы с Gemini AI

### Переменные окружения
- `GEMINI_API_KEY` - ключ API для Gemini AI

## Структура файлов

```
Bot-Doc/
├── services/
│   ├── document_parser_service.py    # Анализ реквизитов
│   └── document_generator_service.py # Генерация документов
├── handlers/
│   └── document_handler.py           # Интеграция в бота
├── templates/
│   └── template_test.docx            # Тестовый шаблон
├── config/locales/
│   ├── en.py                         # Английские тексты
│   └── ru.py                         # Русские тексты
└── test_document_system.py           # Тестовый скрипт
```

## Обработка ошибок

Система включает обработку следующих ошибок:
- Отсутствие GEMINI_API_KEY
- Ошибки парсинга JSON от Gemini
- Отсутствие шаблона документа
- Ошибки генерации документа
- Ошибки отправки файла в Telegram

## Логирование

Все операции логируются в консоль с соответствующими эмодзи:
- ✅ Успешные операции
- ❌ Ошибки
- ⏳ Процессы в работе
- 📄 Информация о документах
