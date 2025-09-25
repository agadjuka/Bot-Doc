"""
Template Management Handler for Telegram Bot
Handles template upload, analysis, and management workflow
"""
import logging
import asyncio
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.error import BadRequest

from config.settings import BotConfig
from services.template_processor_service import TemplateProcessorService
from services.storage_service import StorageService
from services.firestore_service import FirestoreService

logger = logging.getLogger(__name__)


class TemplateManagementHandler:
    """Handler for template management operations"""
    
    def __init__(self, config: BotConfig, firestore_service: Optional[FirestoreService] = None):
        """
        Initialize TemplateManagementHandler
        
        Args:
            config: Bot configuration
            firestore_service: Firestore service instance
        """
        self.config = config
        self.firestore_service = firestore_service
        self.template_processor = TemplateProcessorService()
        self.storage_service = StorageService(
            bucket_name=config.STORAGE_BUCKET_NAME,
            project_id=config.PROJECT_ID
        )
    
    async def templates_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Handle /templates command - show template management menu
        
        Args:
            update: Telegram update
            context: Bot context
            
        Returns:
            Conversation state
        """
        try:
            keyboard = [
                [InlineKeyboardButton("➕ Загрузить новый шаблон", callback_data="upload_template")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "📋 **Управление шаблонами**\n\n"
                "Здесь вы можете загружать и управлять шаблонами документов.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error in templates_command: {e}")
            await update.message.reply_text("❌ Произошла ошибка при загрузке меню шаблонов.")
            return ConversationHandler.END
    
    async def start_template_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Start template upload process
        
        Args:
            update: Telegram update
            context: Bot context
            
        Returns:
            Conversation state
        """
        try:
            query = update.callback_query
            await query.answer()
            
            await query.edit_message_text(
                "📄 **Загрузка нового шаблона**\n\n"
                "Пожалуйста, отправьте мне ваш шаблон в формате .docx",
                parse_mode='Markdown'
            )
            
            return self.config.AWAITING_TEMPLATE_UPLOAD
            
        except Exception as e:
            logger.error(f"Error in start_template_upload: {e}")
            await update.callback_query.edit_message_text("❌ Произошла ошибка при запуске загрузки шаблона.")
            return ConversationHandler.END
    
    async def handle_template_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Handle template file upload and analysis
        
        Args:
            update: Telegram update
            context: Bot context
            
        Returns:
            Conversation state
        """
        try:
            document = update.message.document
            user_id = update.effective_user.id
            
            print(f"📄 [TEMPLATE] Пользователь {user_id} загрузил файл: {document.file_name} ({document.file_size} байт)")
            
            # Check file extension
            if not document.file_name.lower().endswith('.docx'):
                print(f"❌ [TEMPLATE] Неверный формат файла: {document.file_name}")
                await update.message.reply_text(
                    "❌ **Ошибка формата файла**\n\n"
                    "Пожалуйста, отправьте файл в формате .docx",
                    parse_mode='Markdown'
                )
                return self.config.AWAITING_TEMPLATE_UPLOAD
            
            # Send analysis message
            analysis_msg = await update.message.reply_text(
                "⏳ **Анализирую ваш шаблон...**\n\n"
                "Это может занять до минуты.",
                parse_mode='Markdown'
            )
            
            print(f"📥 [TEMPLATE] Скачиваю файл {document.file_name}...")
            # Download file
            file = await context.bot.get_file(document.file_id)
            file_bytes = await file.download_as_bytearray()
            file_bytes = bytes(file_bytes)
            print(f"✅ [TEMPLATE] Файл скачан успешно: {len(file_bytes)} байт")
            
            print(f"🤖 [TEMPLATE] Отправляю файл в Gemini для анализа...")
            # Analyze document
            replacements, field_names = await self.template_processor.analyze_document(file_bytes)
            print(f"✅ [TEMPLATE] Gemini анализ завершен. Найдено полей: {len(field_names)}")
            
            if not field_names:
                print(f"❌ [TEMPLATE] Анализ не удался - поля не найдены")
                await analysis_msg.edit_text(
                    "❌ **Анализ не удался**\n\n"
                    "Не удалось найти поля для заполнения в документе. "
                    "Убедитесь, что в документе есть места для вставки данных.",
                    parse_mode='Markdown'
                )
                return self.config.AWAITING_TEMPLATE_UPLOAD
            
            print(f"🔧 [TEMPLATE] Создаю умный шаблон с {len(replacements)} заменами...")
            # Create smart template
            smart_template_bytes = self.template_processor.create_smart_template(file_bytes, replacements)
            print(f"✅ [TEMPLATE] Умный шаблон создан: {len(smart_template_bytes)} байт")
            
            # Store data in context for later use
            context.user_data['smart_template_bytes'] = smart_template_bytes
            context.user_data['field_names'] = field_names
            context.user_data['original_file_name'] = document.file_name
            
            # Create field list message
            field_list = "\n".join([f"• {field}" for field in field_names])
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ Да, сохранить", callback_data="confirm_template"),
                    InlineKeyboardButton("❌ Отмена", callback_data="cancel_template")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            print(f"📋 [TEMPLATE] Показываю пользователю найденные поля: {field_names}")
            await analysis_msg.edit_text(
                f"✅ **Анализ завершен!**\n\n"
                f"Я нашел в вашем документе следующие поля для заполнения:\n\n"
                f"{field_list}\n\n"
                f"Всё верно?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            return self.config.AWAITING_TEMPLATE_CONFIRMATION
            
        except Exception as e:
            print(f"❌ [TEMPLATE] Ошибка при обработке шаблона: {e}")
            logger.error(f"Error in handle_template_upload: {e}")
            await update.message.reply_text("❌ Произошла ошибка при анализе шаблона.")
            return ConversationHandler.END
    
    async def handle_template_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Handle template confirmation
        
        Args:
            update: Telegram update
            context: Bot context
            
        Returns:
            Conversation state
        """
        try:
            query = update.callback_query
            await query.answer()
            
            if query.data == "cancel_template":
                await query.edit_message_text(
                    "❌ **Загрузка отменена**\n\n"
                    "Шаблон не был сохранен.",
                    parse_mode='Markdown'
                )
                return ConversationHandler.END
            
            elif query.data == "confirm_template":
                await query.edit_message_text(
                    "📝 **Отлично!**\n\n"
                    "Теперь придумайте короткое имя для этого шаблона "
                    "(например, 'Договор на услуги').",
                    parse_mode='Markdown'
                )
                return self.config.AWAITING_TEMPLATE_NAME
            
        except Exception as e:
            logger.error(f"Error in handle_template_confirmation: {e}")
            await update.callback_query.edit_message_text("❌ Произошла ошибка при подтверждении шаблона.")
            return ConversationHandler.END
    
    async def handle_template_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Handle template name input and save template
        
        Args:
            update: Telegram update
            context: Bot context
            
        Returns:
            Conversation state
        """
        try:
            template_name = update.message.text.strip()
            user_id = update.effective_user.id
            
            print(f"💾 [TEMPLATE] Пользователь {user_id} ввел имя шаблона: '{template_name}'")
            
            if not template_name:
                print(f"❌ [TEMPLATE] Пустое имя шаблона от пользователя {user_id}")
                await update.message.reply_text(
                    "❌ **Имя шаблона не может быть пустым**\n\n"
                    "Пожалуйста, введите корректное имя для шаблона.",
                    parse_mode='Markdown'
                )
                return self.config.AWAITING_TEMPLATE_NAME
            
            # Get stored data
            smart_template_bytes = context.user_data.get('smart_template_bytes')
            field_names = context.user_data.get('field_names')
            
            if not smart_template_bytes or not field_names:
                print(f"❌ [TEMPLATE] Данные шаблона потеряны для пользователя {user_id}")
                await update.message.reply_text(
                    "❌ **Ошибка данных**\n\n"
                    "Данные шаблона были потеряны. Пожалуйста, начните загрузку заново.",
                    parse_mode='Markdown'
                )
                return ConversationHandler.END
            
            # Create destination path
            destination_path = f"user_{user_id}/{template_name}.docx"
            print(f"📁 [TEMPLATE] Путь для сохранения: {destination_path}")
            
            print(f"☁️ [TEMPLATE] Загружаю файл в Cloud Storage...")
            # Upload to storage
            upload_success = await self.storage_service.upload_file(
                smart_template_bytes,
                destination_path
            )
            
            if not upload_success:
                print(f"❌ [TEMPLATE] Ошибка загрузки в Cloud Storage")
                await update.message.reply_text(
                    "❌ **Ошибка сохранения**\n\n"
                    "Не удалось сохранить шаблон в облачном хранилище.",
                    parse_mode='Markdown'
                )
                return ConversationHandler.END
            
            print(f"✅ [TEMPLATE] Файл успешно загружен в Cloud Storage")
            
            # Save to Firestore
            if self.firestore_service:
                print(f"🔥 [TEMPLATE] Сохраняю метаданные в Firestore...")
                firestore_success = await self.firestore_service.add_template(
                    user_id=user_id,
                    template_name=template_name,
                    file_path=destination_path,
                    file_type='docx'
                )
                
                if not firestore_success:
                    print(f"⚠️ [TEMPLATE] Предупреждение: не удалось сохранить в Firestore")
                    logger.warning(f"Failed to save template metadata to Firestore for user {user_id}")
                else:
                    print(f"✅ [TEMPLATE] Метаданные сохранены в Firestore")
            else:
                print(f"⚠️ [TEMPLATE] Firestore сервис недоступен")
            
            # Clean up user data
            context.user_data.pop('smart_template_bytes', None)
            context.user_data.pop('field_names', None)
            context.user_data.pop('original_file_name', None)
            print(f"🧹 [TEMPLATE] Очищены данные пользователя {user_id}")
            
            print(f"🎉 [TEMPLATE] Шаблон '{template_name}' успешно сохранен для пользователя {user_id}")
            await update.message.reply_text(
                f"✅ **Шаблон '{template_name}' успешно сохранен!**\n\n"
                f"Теперь вы можете использовать этот шаблон для создания документов.",
                parse_mode='Markdown'
            )
            
            return ConversationHandler.END
            
        except Exception as e:
            print(f"❌ [TEMPLATE] Ошибка при сохранении шаблона: {e}")
            logger.error(f"Error in handle_template_name: {e}")
            await update.message.reply_text("❌ Произошла ошибка при сохранении шаблона.")
            return ConversationHandler.END
    
    async def cancel_template_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Cancel template upload process
        
        Args:
            update: Telegram update
            context: Bot context
            
        Returns:
            Conversation state
        """
        try:
            # Clean up user data
            context.user_data.pop('smart_template_bytes', None)
            context.user_data.pop('field_names', None)
            context.user_data.pop('original_file_name', None)
            
            await update.message.reply_text(
                "❌ **Загрузка отменена**\n\n"
                "Шаблон не был сохранен.",
                parse_mode='Markdown'
            )
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error in cancel_template_upload: {e}")
            return ConversationHandler.END
