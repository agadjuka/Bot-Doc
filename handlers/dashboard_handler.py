"""
Dashboard handler for personal cabinet functionality
Handles template management and user dashboard
"""
import asyncio
from typing import Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CommandHandler, CallbackQueryHandler

from config.settings import BotConfig
from services.firestore_service import get_firestore_service
from config.locales.locale_manager import get_global_locale_manager


class DashboardHandler:
    """Handler for dashboard and template management functionality"""
    
    # FSM States for template addition
    AWAITING_TEMPLATE_FILE = 1
    AWAITING_TEMPLATE_NAME = 2
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.firestore_service = get_firestore_service()
        self.locale_manager = get_global_locale_manager()
    
    async def dashboard_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle /dashboard command - show personal cabinet"""
        user_id = update.effective_user.id
        language = self.locale_manager.get_user_language(user_id)
        
        # Get user's templates
        templates = await self.firestore_service.get_templates(user_id)
        
        # Create dashboard message
        dashboard_text = self._get_dashboard_message(language, templates)
        
        # Create keyboard
        keyboard = self._get_dashboard_keyboard(language)
        
        await update.message.reply_text(
            dashboard_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        return self.config.AWAITING_INPUT
    
    async def add_template_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle 'Add new template' button - start FSM"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        language = self.locale_manager.get_user_language(user_id)
        
        # Set state in context
        context.user_data['state'] = self.AWAITING_TEMPLATE_FILE
        
        # Start template addition FSM
        message_text = self._get_template_file_request_message(language)
        
        await query.edit_message_text(
            message_text,
            parse_mode='HTML'
        )
        
        return self.AWAITING_TEMPLATE_FILE
    
    async def handle_template_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle document file upload for template"""
        user_id = update.effective_user.id
        language = self.locale_manager.get_user_language(user_id)
        
        # Check if it's a document
        if not update.message.document:
            await update.message.reply_text(
                self._get_invalid_file_message(language),
                parse_mode='HTML'
            )
            return self.AWAITING_TEMPLATE_FILE
        
        document = update.message.document
        
        # Check if it's a .docx file
        file_name = document.file_name or ""
        mime_type = document.mime_type or ""
        
        if not (file_name.lower().endswith('.docx') or mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'):
            await update.message.reply_text(
                self._get_invalid_file_type_message(language),
                parse_mode='HTML'
            )
            return self.AWAITING_TEMPLATE_FILE
        
        # Store file_id in context for later use
        context.user_data['template_file_id'] = document.file_id
        context.user_data['template_file_name'] = file_name
        context.user_data['state'] = self.AWAITING_TEMPLATE_NAME
        
        # Ask for template name
        message_text = self._get_template_name_request_message(language)
        
        await update.message.reply_text(
            message_text,
            parse_mode='HTML'
        )
        
        return self.AWAITING_TEMPLATE_NAME
    
    async def handle_template_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle template name input"""
        user_id = update.effective_user.id
        language = self.locale_manager.get_user_language(user_id)
        
        template_name = update.message.text.strip()
        
        if not template_name:
            await update.message.reply_text(
                self._get_empty_name_message(language),
                parse_mode='HTML'
            )
            return self.AWAITING_TEMPLATE_NAME
        
        # Get file_id from context
        file_id = context.user_data.get('template_file_id')
        if not file_id:
            await update.message.reply_text(
                self._get_missing_file_message(language),
                parse_mode='HTML'
            )
            return self.AWAITING_TEMPLATE_NAME
        
        # Save template to Firestore
        success = await self.firestore_service.add_template(
            user_id=user_id,
            template_name=template_name,
            file_id=file_id,
            file_type='docx'
        )
        
        if success:
            # Clear context data
            context.user_data.pop('template_file_id', None)
            context.user_data.pop('template_file_name', None)
            context.user_data.pop('state', None)
            
            # Send success message
            success_message = self._get_template_saved_message(language, template_name)
            await update.message.reply_text(
                success_message,
                parse_mode='HTML'
            )
        else:
            # Send error message
            error_message = self._get_template_save_error_message(language)
            await update.message.reply_text(
                error_message,
                parse_mode='HTML'
            )
        
        return self.config.AWAITING_INPUT
    
    async def my_templates_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle 'My templates' button - show user's templates"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        language = self.locale_manager.get_user_language(user_id)
        
        # Get user's templates
        templates = await self.firestore_service.get_templates(user_id)
        
        if not templates:
            message_text = self._get_no_templates_message(language)
            keyboard = self._get_back_to_dashboard_keyboard(language)
        else:
            message_text = self._get_templates_list_message(language, templates)
            keyboard = self._get_templates_keyboard(language, templates)
        
        await query.edit_message_text(
            message_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        return self.config.AWAITING_INPUT
    
    async def cancel_template_addition(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel template addition and return to dashboard"""
        user_id = update.effective_user.id
        language = self.locale_manager.get_user_language(user_id)
        
        # Clear context data
        context.user_data.pop('template_file_id', None)
        context.user_data.pop('template_file_name', None)
        context.user_data.pop('state', None)
        
        # Send cancellation message
        await update.message.reply_text(
            self._get_template_cancelled_message(language),
            parse_mode='HTML'
        )
        
        return self.config.AWAITING_INPUT
    
    async def back_to_main_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle 'Back to Main Menu' button"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        language = self.locale_manager.get_user_language(user_id)
        
        # Get welcome message and keyboard from message handlers
        from handlers.message_handlers import MessageHandlers
        from services.ai_service import ReceiptAnalysisServiceCompat, AIServiceFactory
        from config.prompts import PromptManager
        
        # Create temporary message handler for welcome message
        prompt_manager = PromptManager()
        ai_factory = AIServiceFactory(self.config, prompt_manager)
        ai_service = ai_factory.get_default_service()
        analysis_service = ReceiptAnalysisServiceCompat(ai_service, ai_factory)
        message_handlers = MessageHandlers(self.config, analysis_service)
        
        welcome_text = message_handlers._get_welcome_message(language)
        keyboard = message_handlers._get_main_keyboard(language)
        
        await query.edit_message_text(
            welcome_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        return self.config.AWAITING_INPUT
    
    async def back_to_dashboard_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle 'Back to Dashboard' button"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        language = self.locale_manager.get_user_language(user_id)
        
        # Get user's templates
        templates = await self.firestore_service.get_templates(user_id)
        
        # Create dashboard message
        dashboard_text = self._get_dashboard_message(language, templates)
        
        # Create keyboard
        keyboard = self._get_dashboard_keyboard(language)
        
        await query.edit_message_text(
            dashboard_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        return self.config.AWAITING_INPUT
    
    def _get_dashboard_message(self, language: str, templates: list) -> str:
        """Get dashboard message based on language"""
        messages = {
            'en': f"""
🏠 <b>Personal Cabinet</b>

📊 <b>Your Statistics:</b>
• Templates: {len(templates)}

📂 <b>Quick Actions:</b>
Use the buttons below to manage your templates.
            """,
            'ru': f"""
🏠 <b>Личный кабинет</b>

📊 <b>Ваша статистика:</b>
• Шаблоны: {len(templates)}

📂 <b>Быстрые действия:</b>
Используйте кнопки ниже для управления вашими шаблонами.
            """
        }
        return messages.get(language, messages['en'])
    
    def _get_dashboard_keyboard(self, language: str) -> InlineKeyboardMarkup:
        """Get dashboard keyboard based on language"""
        buttons = {
            'en': [
                [InlineKeyboardButton("📂 My Templates", callback_data="my_templates")],
                [InlineKeyboardButton("➕ Add New Template", callback_data="add_template")],
                [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]
            ],
            'ru': [
                [InlineKeyboardButton("📂 Мои шаблоны", callback_data="my_templates")],
                [InlineKeyboardButton("➕ Добавить новый шаблон", callback_data="add_template")],
                [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_main")]
            ]
        }
        
        keyboard_buttons = buttons.get(language, buttons['en'])
        return InlineKeyboardMarkup(keyboard_buttons)
    
    def _get_template_file_request_message(self, language: str) -> str:
        """Get template file request message"""
        messages = {
            'en': """
📄 <b>Add New Template</b>

Please send me a template file in .docx format.

<b>Supported formats:</b>
• .docx (Microsoft Word document)

Just upload your file and I'll guide you through the process!
            """,
            'ru': """
📄 <b>Добавить новый шаблон</b>

Пожалуйста, отправьте мне файл шаблона в формате .docx.

<b>Поддерживаемые форматы:</b>
• .docx (документ Microsoft Word)

Просто загрузите ваш файл, и я проведу вас через процесс!
            """
        }
        return messages.get(language, messages['en'])
    
    def _get_invalid_file_message(self, language: str) -> str:
        """Get invalid file message"""
        messages = {
            'en': "❌ Please send a document file, not a photo or other type of file.",
            'ru': "❌ Пожалуйста, отправьте документ, а не фото или другой тип файла."
        }
        return messages.get(language, messages['en'])
    
    def _get_invalid_file_type_message(self, language: str) -> str:
        """Get invalid file type message"""
        messages = {
            'en': "❌ Please send a .docx file. Other formats are not supported.",
            'ru': "❌ Пожалуйста, отправьте файл .docx. Другие форматы не поддерживаются."
        }
        return messages.get(language, messages['en'])
    
    def _get_template_name_request_message(self, language: str) -> str:
        """Get template name request message"""
        messages = {
            'en': """
✅ <b>Great file!</b>

Now please give your template a short name (for example: 'Service Contract' or 'Invoice Template').

This name will help you identify the template later.
            """,
            'ru': """
✅ <b>Отличный файл!</b>

Теперь придумайте для него короткое имя (например, 'Договор услуг' или 'Шаблон счета').

Это имя поможет вам найти шаблон позже.
            """
        }
        return messages.get(language, messages['en'])
    
    def _get_empty_name_message(self, language: str) -> str:
        """Get empty name message"""
        messages = {
            'en': "❌ Please enter a template name. It cannot be empty.",
            'ru': "❌ Пожалуйста, введите имя шаблона. Оно не может быть пустым."
        }
        return messages.get(language, messages['en'])
    
    def _get_missing_file_message(self, language: str) -> str:
        """Get missing file message"""
        messages = {
            'en': "❌ File information is missing. Please start over by uploading a file.",
            'ru': "❌ Информация о файле отсутствует. Пожалуйста, начните заново, загрузив файл."
        }
        return messages.get(language, messages['en'])
    
    def _get_template_saved_message(self, language: str, template_name: str) -> str:
        """Get template saved success message"""
        messages = {
            'en': f"✅ Template '{template_name}' successfully saved!",
            'ru': f"✅ Шаблон '{template_name}' успешно сохранен!"
        }
        return messages.get(language, messages['en'])
    
    def _get_template_save_error_message(self, language: str) -> str:
        """Get template save error message"""
        messages = {
            'en': "❌ Failed to save template. Please try again later.",
            'ru': "❌ Не удалось сохранить шаблон. Попробуйте позже."
        }
        return messages.get(language, messages['en'])
    
    def _get_template_cancelled_message(self, language: str) -> str:
        """Get template cancellation message"""
        messages = {
            'en': "❌ Template addition cancelled. You can try again anytime.",
            'ru': "❌ Добавление шаблона отменено. Вы можете попробовать снова в любое время."
        }
        return messages.get(language, messages['en'])
    
    def _get_no_templates_message(self, language: str) -> str:
        """Get no templates message"""
        messages = {
            'en': """
📂 <b>My Templates</b>

You don't have any templates yet.

Click "Add New Template" to create your first template!
            """,
            'ru': """
📂 <b>Мои шаблоны</b>

У вас пока нет шаблонов.

Нажмите "Добавить новый шаблон", чтобы создать первый шаблон!
            """
        }
        return messages.get(language, messages['en'])
    
    def _get_templates_list_message(self, language: str, templates: list) -> str:
        """Get templates list message"""
        messages = {
            'en': f"""
📂 <b>My Templates</b>

<b>Total templates: {len(templates)}</b>

""",
            'ru': f"""
📂 <b>Мои шаблоны</b>

<b>Всего шаблонов: {len(templates)}</b>

"""
        }
        
        base_message = messages.get(language, messages['en'])
        
        # Add template list
        for i, template in enumerate(templates[:10], 1):  # Show max 10 templates
            template_name = template.get('template_name', 'Unnamed')
            created_at = template.get('created_at')
            if created_at:
                date_str = created_at.strftime('%d.%m.%Y') if hasattr(created_at, 'strftime') else str(created_at)
                base_message += f"{i}. <b>{template_name}</b> ({date_str})\n"
            else:
                base_message += f"{i}. <b>{template_name}</b>\n"
        
        if len(templates) > 10:
            remaining = len(templates) - 10
            more_text = {
                'en': f"\n... and {remaining} more templates",
                'ru': f"\n... и еще {remaining} шаблонов"
            }
            base_message += more_text.get(language, more_text['en'])
        
        return base_message
    
    def _get_templates_keyboard(self, language: str, templates: list) -> InlineKeyboardMarkup:
        """Get templates keyboard"""
        buttons = []
        
        # Add template buttons (max 5 for UI)
        for template in templates[:5]:
            template_name = template.get('template_name', 'Unnamed')
            template_doc_id = template.get('template_doc_id', '')
            if template_doc_id:
                # Truncate long names
                display_name = template_name[:20] + "..." if len(template_name) > 20 else template_name
                buttons.append([InlineKeyboardButton(f"📄 {display_name}", callback_data=f"template_{template_doc_id}")])
        
        # Add back button
        back_text = {
            'en': "🔙 Back to Dashboard",
            'ru': "🔙 Назад в кабинет"
        }
        buttons.append([InlineKeyboardButton(back_text.get(language, back_text['en']), callback_data="back_to_dashboard")])
        
        return InlineKeyboardMarkup(buttons)
    
    def _get_back_to_dashboard_keyboard(self, language: str) -> InlineKeyboardMarkup:
        """Get back to dashboard keyboard"""
        buttons = {
            'en': [
                [InlineKeyboardButton("🔙 Back to Dashboard", callback_data="back_to_dashboard")]
            ],
            'ru': [
                [InlineKeyboardButton("🔙 Назад в кабинет", callback_data="back_to_dashboard")]
            ]
        }
        
        keyboard_buttons = buttons.get(language, buttons['en'])
        return InlineKeyboardMarkup(keyboard_buttons)


def create_dashboard_conversation_handler(config: BotConfig) -> ConversationHandler:
    """Create conversation handler for dashboard functionality"""
    dashboard_handler = DashboardHandler(config)
    
    return ConversationHandler(
        entry_points=[
            CommandHandler("dashboard", dashboard_handler.dashboard_command),
            CallbackQueryHandler(dashboard_handler.add_template_callback, pattern="^add_template$"),
            CallbackQueryHandler(dashboard_handler.my_templates_callback, pattern="^my_templates$"),
            CallbackQueryHandler(dashboard_handler.back_to_main_callback, pattern="^back_to_main$"),
            CallbackQueryHandler(dashboard_handler.back_to_dashboard_callback, pattern="^back_to_dashboard$"),
        ],
        states={
            dashboard_handler.AWAITING_TEMPLATE_FILE: [
                MessageHandler(filters.Document.ALL, dashboard_handler.handle_template_file),
                CommandHandler("cancel", dashboard_handler.cancel_template_addition),
            ],
            dashboard_handler.AWAITING_TEMPLATE_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, dashboard_handler.handle_template_name),
                CommandHandler("cancel", dashboard_handler.cancel_template_addition),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", dashboard_handler.cancel_template_addition),
        ],
        per_message=False
    )
