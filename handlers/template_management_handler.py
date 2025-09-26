"""
Template Management Handler for Telegram Bot
Handles template upload, analysis, and management workflow
"""
import logging
import asyncio
import warnings
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.error import BadRequest

# Подавляем предупреждения PTBUserWarning для более чистого вывода
warnings.filterwarnings("ignore", category=UserWarning, module="telegram")

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
                "Пожалуйста, отправьте мне ваш шаблон в формате .docx или .doc",
                parse_mode='Markdown'
            )
            
            return self.config.AWAITING_TEMPLATE_UPLOAD
            
        except Exception as e:
            logger.error(f"Error in start_template_upload: {e}")
            await update.callback_query.edit_message_text("❌ Произошла ошибка при запуске загрузки шаблона.")
            return ConversationHandler.END
    
    async def handle_template_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Handle template file upload and analysis with new two-file strategy
        
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
            file_name_lower = document.file_name.lower()
            if not (file_name_lower.endswith('.docx') or file_name_lower.endswith('.doc')):
                print(f"❌ [TEMPLATE] Неверный формат файла: {document.file_name}")
                await update.message.reply_text(
                    "❌ **Ошибка формата файла**\n\n"
                    "Пожалуйста, отправьте файл в формате .docx или .doc",
                    parse_mode='Markdown'
                )
                return self.config.AWAITING_TEMPLATE_UPLOAD
            
            # Determine file format
            file_format = '.docx' if file_name_lower.endswith('.docx') else '.doc'
            context.user_data['original_file_format'] = file_format
            
            # Send analysis message
            analysis_msg = await update.message.reply_text(
                "⏳ Анализирую шаблон...",
                parse_mode='Markdown'
            )
            
            print(f"📥 [TEMPLATE] Скачиваю файл {document.file_name}...")
            # Download file
            file = await context.bot.get_file(document.file_id)
            file_bytes = await file.download_as_bytearray()
            file_bytes = bytes(file_bytes)
            print(f"✅ [TEMPLATE] Файл скачан успешно: {len(file_bytes)} байт")
            
            print(f"🤖 [TEMPLATE] Отправляю файл в Gemini для анализа...")
            # Analyze document using new two-file method
            preview_bytes, smart_template_bytes = await self.template_processor.analyze_and_prepare_templates(file_bytes, file_format)
            print(f"✅ [TEMPLATE] Анализ завершен")
            
            if not preview_bytes or not smart_template_bytes:
                print(f"❌ [TEMPLATE] Анализ не удался")
                await analysis_msg.edit_text(
                    "❌ **Анализ не удался**\n\n"
                    "Не удалось проанализировать документ. "
                    "Убедитесь, что в документе есть места для вставки данных.",
                    parse_mode='Markdown'
                )
                return self.config.AWAITING_TEMPLATE_UPLOAD
            
            print(f"✅ [TEMPLATE] Созданы файлы:")
            print(f"   - Предпросмотр: {len(preview_bytes)} байт")
            print(f"   - Умный шаблон: {len(smart_template_bytes)} байт")
            
            # Store both files in FSM storage
            context.user_data['preview_bytes'] = preview_bytes
            context.user_data['smart_template_bytes'] = smart_template_bytes
            context.user_data['original_file_name'] = document.file_name
            
            # Send the preview file as a document immediately
            print(f"📄 [TEMPLATE] Отправляю файл предпросмотра пользователю...")
            from io import BytesIO
            preview_file = BytesIO(preview_bytes)
            preview_file.name = f"preview_{document.file_name}"
            
            await analysis_msg.edit_text(
                "✅ Готово! Я подготовил предпросмотр. Пожалуйста, откройте файл и убедитесь, что я правильно определил поля для заполнения (они выделены красным).\n\n"
                "Если всё верно, придумайте и отправьте мне имя для этого шаблона, чтобы сохранить его. Для отмены просто отправьте новый файл."
            )
            
            await update.message.reply_document(
                document=preview_file,
                caption="📄 Файл предпросмотра готов"
            )
            
            return self.config.AWAITING_TEMPLATE_NAME
            
        except Exception as e:
            print(f"❌ [TEMPLATE] Ошибка при обработке шаблона: {e}")
            logger.error(f"Error in handle_template_upload: {e}")
            await update.message.reply_text("❌ Произошла ошибка при обработке файла.")
            return ConversationHandler.END
    
    async def handle_template_name_and_save(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Handle template name input and save smart template
        
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
            
            # Get stored smart template data
            smart_template_bytes = context.user_data.get('smart_template_bytes')
            
            if not smart_template_bytes:
                print(f"❌ [TEMPLATE] Данные умного шаблона потеряны для пользователя {user_id}")
                await update.message.reply_text(
                    "❌ **Ошибка данных**\n\n"
                    "Данные шаблона были потеряны. Пожалуйста, начните загрузку заново.",
                    parse_mode='Markdown'
                )
                return ConversationHandler.END
            
            # Create destination path with original file format
            original_format = context.user_data.get('original_file_format', '.docx')
            destination_path = f"user_{user_id}/{template_name}{original_format}"
            print(f"📁 [TEMPLATE] Путь для сохранения: {destination_path}")
            
            print(f"☁️ [TEMPLATE] Загружаю умный шаблон в Cloud Storage...")
            # Upload smart template to storage
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
            
            print(f"✅ [TEMPLATE] Умный шаблон успешно загружен в Cloud Storage")
            
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
            context.user_data.pop('preview_bytes', None)
            context.user_data.pop('smart_template_bytes', None)
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
            logger.error(f"Error in handle_template_name_and_save: {e}")
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
            context.user_data.pop('preview_bytes', None)
            context.user_data.pop('smart_template_bytes', None)
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
