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
        return f"""Ты — AI-юрист и эксперт по разметке документов. Тебе предоставлена детальная карта документа, где каждый мельчайший текстовый фрагмент (`run`) имеет уникальный ID в формате `[run-ID]`.

**КАРТА ДОКУМЕНТА:**
---
{document_map}
---

**ТВОЯ ЗАДАЧА — ХИРУРГИЧЕСКОЕ РЕДАКТИРОВАНИЕ КАРТЫ:**

1.  **АНАЛИЗ:** Изучи карту, определи 'Исполнителя' (заполненная сторона-образец) и 'Заказчика' (сторона с пропусками).
2.  **ЗАПРЕТ:** Не изменяй никакие `[run-ID]` и текст, относящиеся к 'Исполнителю'. Эта часть карты неприкосновенна.
3.  **РЕДАКТИРОВАНИЕ:** Найди **текст** внутри `run`-ов, которые являются пропусками (`_______` или желтый текст) и относятся **только** к 'Заказчику'. Выполни следующие замены:
    *   Пропуски, соответствующие **наименованию** в преамбуле, замени на маркер `[Наименование Контрагента]`.
    *   **Каждый** пропуск в блоке **реквизитов** замени на маркер `[Реквизиты Контрагента]`. Если там 10 пустых строк (`run`-ов), каждая из них должна содержать этот маркер.
    *   Пропуск, соответствующий **подписи представителя**, замени на маркер `[ФИО представителя Контрагента]`.
4.  **РЕЗУЛЬТАТ:** Твой ответ — это **ПОЛНАЯ, ИЗМЕНЕННАЯ КОПИЯ ИСХОДНОЙ КАРТЫ**. Ты должен вернуть весь текст карты, сохранив все оригинальные `[run-ID]` и текст 'Исполнителя', но с уже замененным текстом пропусков у 'Заказчика'.

**ПРИМЕР РАБОТЫ:**

**ИСХОДНАЯ КАРТА (фрагмент):**
`...[run-155]ИНН:[run-156] 77... [run-281]ИНН:[run-282]_______...`

**ТВОЙ ОТВЕТ (измененная карта, фрагмент):**
`...[run-155]ИНН:[run-156] 77... [run-281]ИНН:[run-282][Реквизиты Контрагента]...`

Не добавляй никаких комментариев, JSON или объяснений. Только измененная карта."""
    
    def _get_company_info_extraction_prompt(self) -> str:
        """Company info extraction prompt for document parser"""
        return """
Проанализируй текст с реквизитами компании. Извлеки следующие поля: {fields_list}.

Имена ключей в JSON должны быть ТОЧНО ТАКИМИ ЖЕ, как в списке выше. Если поле не найдено, используй null.

Текст для анализа:
{text}

Верни только валидный JSON без дополнительных комментариев или объяснений.
"""