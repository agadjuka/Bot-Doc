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
        return """Ты получишь текст договора в формате Markdown. Он сохраняет структуру таблиц и заголовков. Анализируй его, учитывая эту разметку.

Ты — опытный юрист-аналитик, который должен проанализировать договор и определить, какие поля нужно заполнить для второй стороны (контрагента).

Вот текст договора:
---
{document_text}
---

**ТВОЙ АЛГОРИТМ ДЕЙСТВИЙ:**

**ШАГ 1: ОПРЕДЕЛИ ДВЕ СТОРОНЫ ДОГОВОРА.**
- Проанализируй договор и определи две стороны: одну полностью заполненную сторону (используй её как образец) и вторую сторону с пропусками (контрагента).
- Полностью заполненная сторона содержит все необходимые данные: наименование компании, реквизиты (ИНН, ОГРН, адрес и т.д.), данные подписанта.
- Вторая сторона (контрагент) имеет пропуски, которые нужно определить и классифицировать.

**ШАГ 2: НАЙДИ ВСЕ ОТДЕЛЬНЫЕ ПРОПУСКИ У КОНТРАГЕНТА.**
- Пропуском считается текст, выделенный желтым цветом, или сплошная линия из символов нижнего подчеркивания (`_______`).
- **ВАЖНО**: Определяй КАЖДЫЙ пропуск отдельно, даже если они находятся рядом друг с другом.
- НЕ группируй несколько строк подчеркиваний в один блок - каждая строка это отдельный пропуск.
- Найди ВСЕ пропуски, относящиеся к контрагенту (второй стороне).
- Используй заполненную сторону как образец для понимания структуры и типов данных.

**ШАГ 3: КЛАССИФИЦИРУЙ КАЖДЫЙ ПРОПУСК ПО ТРЕМ ТИПАМ.**
Проанализируй каждый найденный пропуск отдельно и определи его назначение. У тебя есть три типа:

1. **`PARTY_2_NAME`** - Наименование контрагента (название компании/организации):
   - Обычно находится в преамбуле договора
   - Пример: "ООО «Название компании»"
   - Обычно это одна строка подчеркиваний

2. **`PARTY_2_REQUISITES`** - Любое поле реквизитов контрагента:
   - Каждая отдельная строка с реквизитами: ИНН, ОГРН, адрес, банковские реквизиты и т.д.
   - Каждая строка подчеркиваний в разделе реквизитов - это отдельное поле
   - Используй структуру заполненной стороны как образец для понимания, что должно быть в каждой строке

3. **`PARTY_2_DIRECTOR_NAME`** - Лицо, подписывающее договор от контрагента:
   - ФИО и должность представителя контрагента
   - Обычно находится в конце договора в разделе подписей
   - Обычно это одна строка подчеркиваний

**ШАГ 4: СФОРМИРУЙ ИТОГОВЫЙ JSON.**
- Твой ответ должен быть **ТОЛЬКО** валидным JSON-массивом.
- Включи в массив **КАЖДЫЙ** найденный пропуск как отдельный объект.
- Каждый объект должен иметь два ключа:
    - `original_text`: Точный текст одного пропуска (одна строка подчеркиваний)
    - `type`: Один из трех ключей: `PARTY_2_NAME`, `PARTY_2_REQUISITES`, `PARTY_2_DIRECTOR_NAME`

**КРИТИЧЕСКИ ВАЖНО:**
- НЕ группируй несколько строк подчеркиваний в один объект
- Каждая строка подчеркиваний = отдельный объект в JSON
- Если видишь 5 строк подчеркиваний в разделе реквизитов = создай 5 объектов с типом `PARTY_2_REQUISITES`
- НЕ заполняй пропуски конкретными данными - только определяй их тип
- Используй заполненную сторону как образец для понимания структуры
- Будь точным в определении границ каждого пропуска

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