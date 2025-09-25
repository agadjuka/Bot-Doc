"""
Document handler for Telegram bot - Template version
Handles document creation workflow using FSM
"""
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.settings import BotConfig
from services.ai_service import ReceiptAnalysisServiceCompat
from services.document_parser_service import DocumentParserService
from services.document_generator_service import DocumentGeneratorService
from handlers.base_message_handler import BaseMessageHandler
from config.locales.locale_manager import get_global_locale_manager


class DocumentHandler(BaseMessageHandler):
    """Document handler for contract creation workflow"""
    
    def __init__(self, config: BotConfig, analysis_service: ReceiptAnalysisServiceCompat):
        super().__init__(config, analysis_service)
        
        # Initialize LocaleManager
        self.locale_manager = get_global_locale_manager()
        
        # Initialize document services
        self.document_parser = DocumentParserService()
        self.document_generator = DocumentGeneratorService()
    
    async def new_contract_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle /new_contract command - start document creation process"""
        print(f"DEBUG: New contract command received from user {update.effective_user.id}")
        
        # Get user language (default to Russian)
        user_id = update.effective_user.id
        language = self.locale_manager.get_user_language_from_storage(user_id) or 'ru'
        
        # Get localized message
        message_text = self.get_text("document.new_contract_start", language=language)
        
        # Create keyboard with cancel option
        keyboard = self._get_cancel_keyboard(language)
        
        await update.message.reply_text(
            message_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        # Return state for FSM
        return self.config.AWAITING_COMPANY_INFO
    
    async def handle_company_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle company information input when in AWAITING_COMPANY_INFO state"""
        print(f"DEBUG: Company info received from user {update.effective_user.id}")
        
        # Get user language (default to Russian)
        user_id = update.effective_user.id
        language = self.locale_manager.get_user_language_from_storage(user_id) or 'ru'
        
        # Get the company information text
        company_info = update.message.text
        
        try:
            # Send analyzing message
            analyzing_message = await update.message.reply_text("⏳ Анализирую информацию...")
            
            # Parse company information using Gemini
            parsed_data = await self.document_parser.parse_company_info(company_info)
            
            # Check if we got any useful data
            if not any(parsed_data.values()):
                await analyzing_message.edit_text("❌ Не удалось извлечь информацию из текста. Попробуйте еще раз с более подробными данными.")
                return self.config.AWAITING_COMPANY_INFO
            
            # Send data extracted message
            await analyzing_message.edit_text("✅ Данные извлечены. Создаю документ...")
            
            # Generate document
            template_path = self.document_generator.get_template_path("template_test")
            
            # Check if template exists
            if not os.path.exists(template_path):
                await analyzing_message.edit_text("❌ Шаблон документа не найден. Обратитесь к администратору.")
                return self.config.AWAITING_INPUT
            
            # Fill the document with parsed data
            document_bytes = self.document_generator.fill_document(template_path, parsed_data)
            
            # Send the document to user
            await update.message.reply_document(
                document=document_bytes,
                filename="company_info.docx",
                caption="📄 Документ готов! Вот информация о компании в формате Word."
            )
            
            # Delete the analyzing message
            await analyzing_message.delete()
            
            # Send success message
            success_text = self.get_text("document.creation_success", language=language)
            keyboard = self._get_main_menu_keyboard(language)
            
            await update.message.reply_text(
                success_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
        except Exception as e:
            print(f"❌ Ошибка при обработке информации о компании: {e}")
            
            # Send error message
            error_text = f"❌ Произошла ошибка при создании документа: {str(e)}"
            keyboard = self._get_main_menu_keyboard(language)
            
            await update.message.reply_text(
                error_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        
        # Return to main state (end FSM)
        return self.config.AWAITING_INPUT
    
    async def cancel_document_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle cancel button during document creation"""
        print(f"DEBUG: Document creation cancelled by user {update.effective_user.id}")
        
        # Get user language (default to Russian)
        user_id = update.effective_user.id
        language = self.locale_manager.get_user_language_from_storage(user_id) or 'ru'
        
        # Get cancel message
        cancel_text = self.get_text("document.creation_cancelled", language=language)
        
        # Create main menu keyboard
        keyboard = self._get_main_menu_keyboard(language)
        
        await update.message.reply_text(
            cancel_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        # Return to main state
        return self.config.AWAITING_INPUT
    
    def _get_cancel_keyboard(self, language: str) -> InlineKeyboardMarkup:
        """Get cancel keyboard for document creation"""
        buttons = {
            'en': [
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_document")]
            ],
            'ru': [
                [InlineKeyboardButton("❌ Отмена", callback_data="cancel_document")]
            ]
        }
        
        keyboard_buttons = buttons.get(language, buttons['en'])
        return InlineKeyboardMarkup(keyboard_buttons)
    
    def _get_processing_keyboard(self, language: str) -> InlineKeyboardMarkup:
        """Get processing options keyboard"""
        buttons = {
            'en': [
                [InlineKeyboardButton("✅ Continue", callback_data="continue_processing")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_document")]
            ],
            'ru': [
                [InlineKeyboardButton("✅ Продолжить", callback_data="continue_processing")],
                [InlineKeyboardButton("❌ Отмена", callback_data="cancel_document")]
            ]
        }
        
        keyboard_buttons = buttons.get(language, buttons['en'])
        return InlineKeyboardMarkup(keyboard_buttons)
    
    def _get_main_menu_keyboard(self, language: str) -> InlineKeyboardMarkup:
        """Get main menu keyboard"""
        buttons = {
            'en': [
                [InlineKeyboardButton("Help", callback_data="help")],
                [InlineKeyboardButton("Language", callback_data="language")]
            ],
            'ru': [
                [InlineKeyboardButton("Помощь", callback_data="help")],
                [InlineKeyboardButton("Язык", callback_data="language")]
            ]
        }
        
        keyboard_buttons = buttons.get(language, buttons['en'])
        return InlineKeyboardMarkup(keyboard_buttons)
