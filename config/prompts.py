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
    
    def get_document_analysis_prompt(self, document_json_map: str) -> str:
        """Get document analysis prompt with document JSON map"""
        return self._get_document_analysis_prompt(document_json_map)
    
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
    
    def _get_document_analysis_prompt(self, document_json_map: str) -> str:
        # Убедись, что сигнатура метода в PromptManager обновлена
        return f"""Ты — AI-юрист высшей квалификации. Тебе предоставлен "рентгеновский снимок" документа в формате JSON. Он в точности повторяет структуру документа: параграфы, таблицы, строки, ячейки и мельчайшие текстовые фрагменты (`run`-ы) с их ID.

**JSON-КАРТА ДОКУМЕНТА:**
---
{document_json_map}
---

**ТВОЯ ЗАДАЧА — ДЕЙСТВОВАТЬ КАК ЧЕЛОВЕК:**

1.  **ПОЙМИ КОНТЕКСТ:** Изучи всю JSON-карту. Определи две стороны договора: 'Исполнителя' (заполненная сторона-образец) и 'Заказчика' (сторона с пропусками). Обрати внимание на структуру таблиц.
2.  **БУДЬ ИНТУИТИВНЫМ:** Твоя цель — найти все места, которые **логически** должны быть заполнены. Это могут быть `run`-ы с текстом `_______`, желтым выделением, или **даже полностью пустые ячейки/параграфы** в зоне 'Заказчика', если по симметрии с 'Исполнителем' там должны быть данные.
3.  **ПРИВЕДИ В ПОРЯДОК:** Если ты видишь несколько `run`-ов, составляющих один логический пропуск (например, `[run-1]___[run-2] [run-3]___`), воспринимай их как единое целое.
4.  **КЛАССИФИЦИРУЙ ЦЕЛИ:** Каждое найденное место для заполнения классифицируй по одному из трех типов: `Наименование Контрагента`, `Реквизиты Контрагента`, `ФИО представителя Контрагента`.
5.  **СФОРМИРУЙ "ПЛАН ОПЕРАЦИИ":** Верни **ТОЛЬКО** валидный JSON-массив. Каждый объект в массиве — это одна правка.
    - **`run_ids`**: Список ID **всех** `run`-ов, которые составляют один логический пропуск.
    - **`field_name`**: Один из трех типов, который ты определил.

**ПРИМЕР РЕЗУЛЬТАТА:**
```json
[
  {{ "run_ids": ["run-51"], "field_name": "Наименование Контрагента" }},
  {{ "run_ids": ["run-282", "run-283"], "field_name": "Реквизиты Контрагента" }},
  {{ "run_ids": ["run-302", "run-305"], "field_name": "ФИО представителя Контрагента" }}
]
Действуй как умный ассистент, а не как тупой робот. Твоя задача — подготовить документ к идеальному заполнению.
"""
    
    def _get_company_info_extraction_prompt(self) -> str:
        """Company info extraction prompt for document parser"""
        return """
Проанализируй текст с реквизитами компании. Извлеки следующие поля: {fields_list}.

Имена ключей в JSON должны быть ТОЧНО ТАКИМИ ЖЕ, как в списке выше. Если поле не найдено, используй null.

Текст для анализа:
{text}

Верни только валидный JSON без дополнительных комментариев или объяснений.
"""