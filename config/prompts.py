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
            'document_analysis': self._get_document_analysis_prompt(),
            'company_info_extraction': self._get_company_info_extraction_prompt()
        }
    
    def get_basic_chat_prompt(self) -> str:
        """Get the basic chat prompt for template"""
        return self._prompts['basic_chat']
    
    def get_ai_response_prompt(self, user_text: str, language: str = "en") -> str:
        """Get AI response prompt with user text and language"""
        return self._prompts['ai_response'].format(user_text=user_text, language=language)
    
    def get_document_analysis_prompt(self, document_text: str) -> str:
        """Get document analysis prompt with document text"""
        try:
            # Escape curly braces in document text to prevent format() errors
            escaped_document_text = document_text.replace('{', '{{').replace('}', '}}')
            return self._prompts['document_analysis'].format(document_text=escaped_document_text)
        except KeyError as e:
            # If there are still format errors, use string replacement instead
            logger.error(f"Format error in document analysis prompt: {e}")
            prompt_template = self._prompts['document_analysis']
            return prompt_template.replace('{document_text}', escaped_document_text)
    
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
    
    def _get_document_analysis_prompt(self) -> str:
        """Document analysis prompt for template processor"""
        return """Ты получишь текст документа в формате Markdown. Он сохраняет структуру таблиц и заголовков. Анализируй его, учитывая эту разметку.

Ты — высокоточный робот-ассистент для разметки документов. Твоя единственная задача — следовать инструкциям с абсолютной точностью. Не думай, не интерпретируй, просто выполняй.

Вот текст документа:
---
{document_text}
---

**ТВОЙ АЛГОРИТМ ДЕЙСТВИЙ:**

**ШАГ 1: ОПРЕДЕЛИ ЗОНЫ РАБОТЫ.**
- В документе есть две колонки или секции для реквизитов: одна для 'ИСПОЛНИТЕЛЯ', другая для 'ЗАКАЗЧИКА'.
- Твоя рабочая зона — **ИСКЛЮЧИТЕЛЬНО** та часть текста, которая находится под заголовком 'ЗАКАЗЧИК:'. Всё, что относится к 'ИСПОЛНИТЕЛЮ', для тебя не существует. **ЗАПРЕЩЕНО** анализировать или изменять текст в зоне 'ИСПОЛНИТЕЛЯ'.

**ШАГ 2: НАЙДИ ПРОПУСКИ В РАБОЧЕЙ ЗОНЕ.**
- Пропуском считается **только** текст, выделенный желтым цветом, или сплошная линия из символов нижнего подчеркивания (`_______`).
- **ЗАПРЕЩЕНО** считать пропусками или изменять заголовки ('ЗАКАЗЧИК:', 'ИСПОЛНИТЕЛЬ:' и т.д.), если они не выделены желтым или не являются подчеркиванием.

**ШАГ 3: СОПОСТАВЬ ПРОПУСКИ С ТРЕМЯ ТИПАМИ ЦЕЛЕЙ.**
- Проанализируй **каждый** найденный пропуск и определи его назначение. У тебя есть всего три возможных типа цели:
    1.  **`PARTY_2_NAME`**: Это наименование 'ЗАКАЗЧИКА' в самом начале документа (в преамбуле).
    2.  **`PARTY_2_DIRECTOR_NAME`**: Это ФИО представителя 'ЗАКАЗЧИКА' в самом низу документа, рядом с местом для подписи.
    3.  **`PARTY_2_REQUISITES`**: Это **ВЕСЬ БЛОК** пустых желтых строк в секции реквизитов под заголовком 'ЗАКАЗЧИК:'. Ты должен найти весь этот блок и пометить его целиком как одну сущность. **НЕ ПЫТАЙСЯ** анализировать каждую строку в этом блоке отдельно.

**ШАГ 4: СФОРМИРУЙ ИТОГОВЫЙ JSON.**
- Твой ответ должен быть **ТОЛЬКО** валидным JSON-массивом.
- Массив должен содержать **ровно три объекта**, по одному на каждый тип цели.
- Если ты не нашел пропуск для какого-то типа (например, имя директора уже вписано), НЕ включай этот объект в массив.
- Каждый объект должен иметь два ключа:
    - `original_text`: Точный текст пропуска, который ты нашел. Для реквизитов это будет весь многострочный блок пустых строк.
    - `type`: Один из трех строгих ключей: `PARTY_2_NAME`, `PARTY_2_REQUISITES`, `PARTY_2_DIRECTOR_NAME`.

**ПРИМЕР РАБОТЫ:**
- Если ты видишь блок:
  `«ЗАКАЗЧИК»:`
  `[желтая_строка_1]`
  `[желтая_строка_2]`
- Ты должен определить `original_text` как `[желтая_строка_1]\n[желтая_строка_2]` и присвоить ему `type: 'PARTY_2_REQUISITES'`. Ты **НЕ ДОЛЖЕН** включать `«ЗАКАЗЧИК»:` в `original_text`.

Выполни этот алгоритм."""
    
    def _get_company_info_extraction_prompt(self) -> str:
        """Company info extraction prompt for document parser"""
        return """
Проанализируй текст с реквизитами компании. Извлеки следующие поля: {fields_list}.

Имена ключей в JSON должны быть ТОЧНО ТАКИМИ ЖЕ, как в списке выше. Если поле не найдено, используй null.

Текст для анализа:
{text}

Верни только валидный JSON без дополнительных комментариев или объяснений.
"""