"""
Message handlers for Telegram bot - Template version
"""
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.settings import BotConfig
from services.ai_service import ReceiptAnalysisServiceCompat
from handlers.base_message_handler import BaseMessageHandler
from config.locales.locale_manager import get_global_locale_manager


class MessageHandlers(BaseMessageHandler):
    """Main message handlers coordinator - template version"""
    
    def __init__(self, config: BotConfig, analysis_service: ReceiptAnalysisServiceCompat):
        super().__init__(config, analysis_service)
        
        # Initialize LocaleManager
        self.locale_manager = get_global_locale_manager()
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle /start command"""
        print(f"DEBUG: Start command received from user {update.effective_user.id}")
        
        # Get user language
        user_id = update.effective_user.id
        language = self.locale_manager.get_user_language(user_id)
        
        # Welcome message
        welcome_text = self._get_welcome_message(language)
        
        # Create keyboard
        keyboard = self._get_main_keyboard(language)
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        return self.config.AWAITING_INPUT
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle /help command"""
        user_id = update.effective_user.id
        language = self.locale_manager.get_user_language(user_id)
        
        help_text = self._get_help_message(language)
        
        await update.message.reply_text(
            help_text,
            parse_mode='HTML'
        )
        
        return self.config.AWAITING_INPUT
    
    async def dashboard_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle /dashboard command - redirect to dashboard handler"""
        from handlers.dashboard_handler import DashboardHandler
        
        # Create dashboard handler instance
        dashboard_handler = DashboardHandler(self.config)
        
        # Call the dashboard_command method
        return await dashboard_handler.dashboard_command(update, context)
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle text messages"""
        user_id = update.effective_user.id
        language = self.locale_manager.get_user_language(user_id)
        
        # Simple echo with AI response
        user_text = update.message.text
        
        # Get AI response
        try:
            ai_response = await self._get_ai_response(user_text, language)
            await update.message.reply_text(ai_response, parse_mode='HTML')
        except Exception as e:
            print(f"Error getting AI response: {e}")
            await update.message.reply_text(
                self._get_error_message(language),
                parse_mode='HTML'
            )
        
        return self.config.AWAITING_INPUT
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle document uploads - redirect to dashboard handler for template processing"""
        from handlers.dashboard_handler import DashboardHandler
        
        # Create dashboard handler instance
        dashboard_handler = DashboardHandler(self.config)
        
        # Check if user is in template addition state
        if context.user_data.get('state') == dashboard_handler.AWAITING_TEMPLATE_FILE:
            return await dashboard_handler.handle_template_file(update, context)
        else:
            # If not in template state, show message about using dashboard
            user_id = update.effective_user.id
            language = self.locale_manager.get_user_language(user_id)
            
            message_text = {
                'en': "📄 <b>Document Upload</b>\n\nTo add a template, please use the Personal Cabinet:\n1. Click 'Personal Cabinet' button\n2. Click 'Add New Template'\n3. Upload your .docx or .doc file",
                'ru': "📄 <b>Загрузка документа</b>\n\nЧтобы добавить шаблон, используйте Личный кабинет:\n1. Нажмите кнопку 'Личный кабинет'\n2. Нажмите 'Добавить новый шаблон'\n3. Загрузите ваш .docx или .doc файл"
            }
            
            await update.message.reply_text(
                message_text.get(language, message_text['en']),
                parse_mode='HTML'
            )
            
            return self.config.AWAITING_INPUT
    
    def _get_welcome_message(self, language: str) -> str:
        """Get welcome message based on language"""
        messages = {
            'en': """
🤖 <b>Welcome to AI Bot Template!</b>

This is a basic template for creating Telegram bots with AI capabilities.

<b>Available commands:</b>
/start - Start the bot
/help - Show help information

Just send me a message and I'll respond using AI!
            """,
            'ru': """
🤖 <b>Добро пожаловать в AI Bot Template!</b>

Это базовый шаблон для создания Telegram ботов с возможностями ИИ.

<b>Доступные команды:</b>
/start - Запустить бота
/help - Показать справку

Просто отправьте мне сообщение, и я отвечу с помощью ИИ!
            """
        }
        return messages.get(language, messages['en'])
    
    def _get_help_message(self, language: str) -> str:
        """Get help message based on language"""
        messages = {
            'en': """
<b>Help - AI Bot Template</b>

This bot can:
• Respond to text messages using AI
• Support multiple languages
• Provide basic conversation capabilities

<b>Commands:</b>
/start - Start the bot
/help - Show this help

<b>Usage:</b>
Just send any text message and the bot will respond using AI!
            """,
            'ru': """
<b>Справка - AI Bot Template</b>

Этот бот может:
• Отвечать на текстовые сообщения с помощью ИИ
• Поддерживать несколько языков
• Обеспечивать базовые возможности общения

<b>Команды:</b>
/start - Запустить бота
/help - Показать эту справку

<b>Использование:</b>
Просто отправьте любое текстовое сообщение, и бот ответит с помощью ИИ!
            """
        }
        return messages.get(language, messages['en'])
    
    def _get_main_keyboard(self, language: str) -> InlineKeyboardMarkup:
        """Get main keyboard based on language"""
        buttons = {
            'en': [
                [InlineKeyboardButton("🏠 Personal Cabinet", callback_data="dashboard")],
                [InlineKeyboardButton("Help", callback_data="help")],
                [InlineKeyboardButton("Language", callback_data="language")]
            ],
            'ru': [
                [InlineKeyboardButton("🏠 Личный кабинет", callback_data="dashboard")],
                [InlineKeyboardButton("Помощь", callback_data="help")],
                [InlineKeyboardButton("Язык", callback_data="language")]
            ]
        }
        
        keyboard_buttons = buttons.get(language, buttons['en'])
        return InlineKeyboardMarkup(keyboard_buttons)
    
    def _get_error_message(self, language: str) -> str:
        """Get error message based on language"""
        messages = {
            'en': "Sorry, I encountered an error. Please try again later.",
            'ru': "Извините, произошла ошибка. Попробуйте позже."
        }
        return messages.get(language, messages['en'])
    
    async def _get_ai_response(self, user_text: str, language: str) -> str:
        """Get AI response for user text"""
        try:
            # Use the analysis service to get AI response
            response = await self.analysis_service.get_ai_response(
                user_text,
                language=language
            )
            return response
        except Exception as e:
            print(f"Error in AI response: {e}")
            return self._get_error_message(language)
