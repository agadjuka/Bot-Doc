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
        # Убедись, что сигнатура метода в PromptManager обновлена
        return f"""Ты — AI-юрист, эксперт по анализу юридических документов. Тебе предоставлена детальная карта документа, где каждый мельчайший текстовый фрагмент (`run`) имеет уникальный ID в формате `[run-ID]`.

**КАРТА ДОКУМЕНТА:**
---
{document_map}
---

**ТВОЯ ЗАДАЧА:**

Проанализируй документ и найди все поля, которые должны быть заполнены данными. Определи, к какому из трех типов относится каждое поле:

1. **"наименование организации"** - название компании, организации
2. **"реквизиты"** - все официальные данные организации (ИНН, ОГРН, юридический адрес, телефон, банковские реквизиты и т.д.)
3. **"ФИО представителя"** - имя, фамилия, отчество представителя организации

**КРИТИЧЕСКИ ВАЖНО - ОБРАБОТКА СТРОК:**

- Если видишь строку с подчеркиваниями (`_______`) или желтыми выделениями, которая предназначена для реквизитов, то:
  - **Первый `run` в строке** замени на "реквизиты"
  - **Остальные `run`-ы в этой строке** замени на пустую строку (очисти их)
- Если это строка для названия компании:
  - **Первый `run` в строке** замени на "наименование организации"
  - **Остальные `run`-ы в этой строке** замени на пустую строку (очисти их)
- Если это строка для имени представителя:
  - **Первый `run` в строке** замени на "ФИО представителя"
  - **Остальные `run`-ы в этой строке** замени на пустую строку (очисти их)

**ПРАВИЛА ОБРАБОТКИ:**

- При замене **полностью удаляй** все подчеркивания, желтые выделения и другой текст
- В строке должно остаться **только одно название поля**, остальные части строки должны быть пустыми

**РЕЗУЛЬТАТ:**
Верни **ТОЛЬКО** валидный JSON-массив. Каждый объект содержит:
- `run_id`: ID фрагмента для замены
- `field_name`: один из трех типов полей

**ПРИМЕР:**
```json
[
  {{ "run_id": "run-25", "field_name": "наименование организации" }},
  {{ "run_id": "run-26", "field_name": "" }},
  {{ "run_id": "run-156", "field_name": "реквизиты" }},
  {{ "run_id": "run-157", "field_name": "" }},
  {{ "run_id": "run-158", "field_name": "" }},
  {{ "run_id": "run-200", "field_name": "ФИО представителя" }}
]
```

**ПОМНИ:** Если строка содержит подчеркивания или выделения, первый `run` замени на название поля, а остальные `run`-ы в строке очисти (замени на пустую строку). В результате в строке должно остаться только одно название поля!"""
    
    def _get_company_info_extraction_prompt(self) -> str:
        """Company info extraction prompt for document parser"""
        return """
Проанализируй текст с реквизитами компании. Извлеки следующие поля: {fields_list}.

Имена ключей в JSON должны быть ТОЧНО ТАКИМИ ЖЕ, как в списке выше. Если поле не найдено, используй null.

Текст для анализа:
{text}

Верни только валидный JSON без дополнительных комментариев или объяснений.
"""