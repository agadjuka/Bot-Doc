"""
Document handler for Telegram bot - Template version
Handles document creation workflow using FSM
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.settings import BotConfig
from services.ai_service import ReceiptAnalysisServiceCompat
from handlers.base_message_handler import BaseMessageHandler
from config.locales.locale_manager import get_global_locale_manager


class DocumentHandler(BaseMessageHandler):
    """Document handler for contract creation workflow"""
    
    def __init__(self, config: BotConfig, analysis_service: ReceiptAnalysisServiceCompat):
        super().__init__(config, analysis_service)
        
        # Initialize LocaleManager
        self.locale_manager = get_global_locale_manager()
    
    async def new_contract_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle /new_contract command - start document creation process"""
        print(f"DEBUG: New contract command received from user {update.effective_user.id}")
        
        # Get user language
        user_id = update.effective_user.id
        language = self.locale_manager.get_user_language(user_id)
        
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
        
        # Get user language
        user_id = update.effective_user.id
        language = self.locale_manager.get_user_language(user_id)
        
        # Get the company information text
        company_info = update.message.text
        
        # Store company info in context for later processing
        context.user_data['company_info'] = company_info
        
        # Get confirmation message
        confirmation_text = self.get_text("document.info_received", language=language)
        
        # Create keyboard with options
        keyboard = self._get_processing_keyboard(language)
        
        await update.message.reply_text(
            confirmation_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        # Return to main state (end FSM)
        return self.config.AWAITING_INPUT
    
    async def cancel_document_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle cancel button during document creation"""
        print(f"DEBUG: Document creation cancelled by user {update.effective_user.id}")
        
        # Get user language
        user_id = update.effective_user.id
        language = self.locale_manager.get_user_language(user_id)
        
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
