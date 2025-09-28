"""
AI prompts configuration for the AI Bot
Contains all prompts used for Gemini AI interactions
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class PromptManager:
    """Manager for AI prompts with methods to get specific prompts"""
    
    def __init__(self):
        self._prompts = self._initialize_prompts()
    
    def _initialize_prompts(self) -> Dict[str, str]:
        """Initialize all prompts used in the project"""
        return {
            'basic_chat': self._get_basic_chat_prompt(),
            'ai_response': self._get_ai_response_prompt(),
            'company_info_extraction': self._get_company_info_extraction_prompt()
        }
    
    def get_basic_chat_prompt(self) -> str:
        """Get the basic chat prompt for template"""
        return self._prompts['basic_chat']
    
    def get_ai_response_prompt(self, user_text: str, language: str = "en") -> str:
        """Get AI response prompt with user text and language"""
        return self._prompts['ai_response'].format(user_text=user_text, language=language)
    
    def get_document_analysis_prompt(self, document_map: str) -> str:
        """Get document analysis prompt with document map"""
        return self._get_document_analysis_prompt(document_map)
    
    def get_company_info_extraction_prompt(self, fields_list: str, text: str) -> str:
        """Get company info extraction prompt with fields list and text"""
        # Escape curly braces in text to prevent format() errors
        escaped_text = text.replace('{', '{{').replace('}', '}}')
        return self._prompts['company_info_extraction'].format(fields_list=fields_list, text=escaped_text)
    
    def _get_basic_chat_prompt(self) -> str:
        """Basic chat prompt for template bot"""
        return """
You are a helpful AI assistant. You can help users with various tasks and answer questions.

Be friendly, helpful, and provide accurate information. If you don't know something, say so honestly.

Keep responses concise but informative.
"""
    
    def _get_ai_response_prompt(self) -> str:
        """AI response prompt for basic conversation"""
        return """
You are a helpful AI assistant. Respond to the user's message in a friendly and helpful way.

User message: {user_text}
Language: {language}

Please respond in {language} language.
"""
    
    def _get_document_analysis_prompt(self, document_map: str) -> str:
        return f"""Ты — AI-юрист, эксперт по анализу юридических документов. Проанализируй документ как профессиональный юрист и найди незаполненные поля, которые нужно заполнить.

**КАРТА ДОКУМЕНТА:**
---
{document_map}
---

**ЗАДАЧА:** Определи, у какой из сторон договора есть незаполненные поля (с подчеркиваниями или выделениями), которые действительно нужно заполнить. Сравни заполненность полей у разных сторон - заполняй только те пустые поля, которые логически должны быть заполнены в контексте договора.

**ТИПЫ ПОЛЕЙ:**
1. **"наименование организации"** - название компании
2. **"реквизиты"** - официальные данные организации (ИНН, ОГРН, адрес, банковские реквизиты)
3. **"ФИО представителя"** - имя представителя организации

**ПРАВИЛА АНАЛИЗА:**
- **Понимай структуру документа** - если видишь таблицу реквизитов, каждая строка предназначена для заполнения реквизитов, независимо от пробелов или разрывов
- **Игнорируй форматирование** - пробелы в начале строк, разрывы внутри строк не меняют назначение поля
- **Фокусируйся на логике** - пустые поля подчеркиваний/выделений в контексте реквизитов = поле для реквизитов
- **ВАЖНО: В таблице реквизитов каждая строка = одно поле для реквизитов, даже если она разбита на части**
- **Анализируй ячейки таблицы целиком** - если ячейка начинается с пробела, это форматирование, которое нужно убрать
- **Смежные run'ы с пробелами** в контексте поля = один логический блок
- **Обрабатывай блоки умно** - для каждого блока подчеркиваний/выделений:
  - **Первый `run`** в блоке замени на соответствующий тип поля
  - **Остальные `run`-ы** в том же блоке очисти (пустая строка)
  - **Пробелы и разрывы** в том же блоке тоже очищай (пустая строка)
  - **НЕ ТРОГАЙ** другие части строки вне блока

**РЕЗУЛЬТАТ:** Верни только валидный JSON-массив. Для каждого блока подчеркиваний/выделений указывай ВСЕ run'ы в блоке:
```json
[
  {{ "run_id": "run-25", "field_name": "наименование организации" }},
  {{ "run_id": "run-26", "field_name": "" }},
  {{ "run_id": "run-27", "field_name": "" }},
  {{ "run_id": "run-156", "field_name": "реквизиты" }}
]
```"""
    
    def _get_company_info_extraction_prompt(self) -> str:
        """Company info extraction prompt for document parser"""
        return """
Проанализируй текст с реквизитами компании. Извлеки следующие поля: {fields_list}.

Имена ключей в JSON должны быть ТОЧНО ТАКИМИ ЖЕ, как в списке выше. Если поле не найдено, используй null.

Текст для анализа:
{text}

Верни только валидный JSON без дополнительных комментариев или объяснений.
"""