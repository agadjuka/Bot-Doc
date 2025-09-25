# TemplateProcessorService

Сервис для автоматического поиска и разметки полей для заполнения в документах.

## Описание

`TemplateProcessorService` использует Google Gemini AI для анализа документов и автоматического определения полей, которые нужно заполнить данными о компании-контрагенте.

## Возможности

- Анализ текста документов на предмет полей для заполнения
- Анализ DOCX файлов (с извлечением текста)
- Автоматическое создание плейсхолдеров в формате `{{field_name}}`
- Генерация человекопонятных названий полей на русском языке
- Интеграция с Google Cloud аутентификацией

## Использование

### Инициализация

```python
from services.template_processor_service import TemplateProcessorService

# Сервис автоматически использует Google Cloud аутентификацию
service = TemplateProcessorService()
```

### Анализ текста

```python
# Анализ текста напрямую
text = "Договор № _____ между ООО 'Компания' и ________________"
replacements, field_names = await service.analyze_text(text)

# replacements: {'_____': '{contract_number}', '________________': '{company_name}'}
# field_names: ['Номер договора', 'Название компании']
```

### Анализ DOCX файла

```python
# Анализ DOCX файла
with open('document.docx', 'rb') as f:
    file_bytes = f.read()

replacements, field_names = await service.analyze_document(file_bytes)
```

## Возвращаемые данные

### replacements (Dict[str, str])
Словарь, где:
- **Ключ**: оригинальный текст из документа
- **Значение**: плейсхолдер для замены

### field_names (List[str])
Список человекопонятных названий полей на русском языке

## Пример результата

```python
replacements = {
    'ДОГОВОР № _____': '{contract_number}',
    'ООО "Контрагент"': '{contractor_legal_name}',
    '________________': '{director_name}'
}

field_names = [
    'Номер договора',
    'Полное наименование контрагента',
    'ФИО директора'
]
```

## Требования

- Google Cloud аутентификация (через `GOOGLE_APPLICATION_CREDENTIALS`)
- Библиотека `python-docx` для работы с DOCX файлами
- Библиотека `google-generativeai` для работы с Gemini AI

## Обработка ошибок

Сервис включает обработку ошибок для:
- Отсутствующих учетных данных Google Cloud
- Ошибок чтения DOCX файлов
- Ошибок API Gemini
- Ошибок парсинга JSON ответов

В случае ошибки возвращается пустой словарь и список.
