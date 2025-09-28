"""
Main entry point for the AI Bot application - LOCAL DEVELOPMENT VERSION
Uses polling instead of webhook for local development
"""
import logging
import asyncio
import os
import warnings
from dotenv import load_dotenv

# Подавляем предупреждения PTBUserWarning для более чистого вывода
warnings.filterwarnings("ignore", category=UserWarning, module="telegram")
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
)
from telegram.error import Conflict, NetworkError
from config.locales.locale_manager import initialize_locale_manager

# КРИТИЧЕСКИ ВАЖНО: Загружаем переменные окружения ПЕРВЫМ ДЕЛОМ
# Используем абсолютный путь к файлу env.local
env_path = os.path.join(os.path.dirname(__file__), "env.local")
print(f"🔍 Загружаем переменные окружения из: {env_path}")
load_dotenv(env_path)

# АВТОМАТИЧЕСКАЯ НАСТРОЙКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ
def setup_environment():
    """Автоматически настраивает переменные окружения для работы бота"""
    
    # Проверяем BOT_TOKEN
    bot_token = os.environ.get("BOT_TOKEN")
    
    # Если токен не найден, пробуем загрузить напрямую из файла
    if not bot_token:
        print("⚠️ BOT_TOKEN не найден в переменных окружения, пробуем загрузить из файла...")
        try:
            env_file_path = os.path.join(os.path.dirname(__file__), "env.local")
            if os.path.exists(env_file_path):
                with open(env_file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip().startswith('BOT_TOKEN='):
                            bot_token = line.strip().split('=', 1)[1]
                            os.environ["BOT_TOKEN"] = bot_token
                            print(f"✅ BOT_TOKEN загружен")
                            break
        except Exception as e:
            print(f"❌ Ошибка при чтении файла env.local: {e}")
    
    if not bot_token:
        print("❌ BOT_TOKEN не найден в переменных окружения!")
        print("💡 Проверьте файл env.local")
        print(f"💡 Путь к файлу: {os.path.join(os.path.dirname(__file__), 'env.local')}")
        return False
    else:
        print(f"✅ BOT_TOKEN найден")
    
    # Путь к файлу с учетными данными
    credentials_path = os.path.join(os.path.dirname(__file__), "bot-doc-473208-706e6adceee1.json")
    
    # Проверяем, существует ли файл с учетными данными
    if os.path.exists(credentials_path):
        # Устанавливаем переменную окружения если она не установлена
        if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
            print(f"✅ GOOGLE_APPLICATION_CREDENTIALS установлена: {credentials_path}")
        else:
            print(f"✅ GOOGLE_APPLICATION_CREDENTIALS уже установлена: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')}")
    else:
        print(f"❌ Файл с учетными данными не найден: {credentials_path}")
        return False
    
    # Устанавливаем имя базы данных Firestore
    if not os.environ.get("FIRESTORE_DATABASE"):
        os.environ["FIRESTORE_DATABASE"] = "docbot"
        print("✅ FIRESTORE_DATABASE установлена: docbot")
    else:
        print(f"✅ FIRESTORE_DATABASE уже установлена: {os.environ.get('FIRESTORE_DATABASE')}")
    
    return True

# Настраиваем переменные окружения
print("🔧 Настройка переменных окружения...")
if not setup_environment():
    print("❌ Не удалось настроить переменные окружения")
    exit(1)

# Инициализация клиента Firestore
# Этот код будет работать автоматически в Cloud Run
# и при локальной настройке с переменной окружения.
from google.cloud import firestore

# Инициализация клиента Firestore с обработкой ошибок
try:
    # Получаем имя базы данных из переменных окружения
    database_name = os.getenv("FIRESTORE_DATABASE", "docbot")
    db = firestore.Client(database=database_name)
    print(f"✅ Firestore клиент инициализирован успешно (база: {database_name})")
except Exception as e:
    print(f"❌ Ошибка инициализации Firestore: {e}")
    print("💡 Убедитесь, что переменная GOOGLE_APPLICATION_CREDENTIALS установлена")
    print(f"💡 Текущее значение: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'НЕ УСТАНОВЛЕНО')}")
    db = None

# OpenCV removed for template - not needed for basic bot functionality
opencv_available = False

from config.settings import BotConfig
from config.prompts import PromptManager
from services.ai_service import AIService, ReceiptAnalysisServiceCompat, AIServiceFactory
from handlers.message_handlers import MessageHandlers
from handlers.callback_handlers import CallbackHandlers
from handlers.document_handler import DocumentHandler
from handlers.dashboard_handler import create_dashboard_conversation_handler
from handlers.template_management_handler import TemplateManagementHandler
from services.firestore_service import get_firestore_service
# MessageSender removed for template
# Google Sheets handler removed for template


def safe_start_bot(application: Application, max_retries: int = 3) -> None:
    """Безопасный запуск бота с обработкой конфликтов"""
    for attempt in range(max_retries):
        try:
            print(f"Попытка запуска бота #{attempt + 1}...")
            
            # Сброс webhook перед каждым запуском
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(application.bot.delete_webhook(drop_pending_updates=True))
                print("✅ Webhook сброшен успешно")
            except Exception as e:
                print(f"⚠️ Предупреждение при сбросе webhook: {e}")
            
            # Небольшая задержка перед запуском
            import time
            time.sleep(2)
            
            # Запуск бота
            application.run_polling()
            break
            
        except Conflict as e:
            print(f"❌ Конфликт обнаружен (попытка {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5  # Увеличиваем время ожидания с каждой попыткой
                print(f"⏳ Ожидание {wait_time} секунд перед следующей попыткой...")
                time.sleep(wait_time)
            else:
                print("❌ Максимальное количество попыток исчерпано. Проверьте, что не запущено других экземпляров бота.")
                raise
                
        except NetworkError as e:
            print(f"🌐 Ошибка сети (попытка {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                wait_time = 3
                print(f"⏳ Ожидание {wait_time} секунд перед повторной попыткой...")
                time.sleep(wait_time)
            else:
                raise
                
        except Exception as e:
            print(f"❌ Неожиданная ошибка: {e}")
            raise


# Cleanup function removed for template - not needed for basic bot functionality

def main() -> None:
    """Main function to start the bot"""
    # Токен уже проверен в setup_environment()
    
    # Initialize configuration
    config = BotConfig()
    prompt_manager = PromptManager()
    
    # Initialize AI Service Factory for dual model support
    ai_factory = AIServiceFactory(config, prompt_manager)
    
    # Get default AI service (Pro model)
    ai_service = ai_factory.get_default_service()
    analysis_service = ReceiptAnalysisServiceCompat(ai_service, ai_factory)
    
    print(f"🤖 AI Service инициализирован: {ai_service.get_current_model_info()['name']}")
    print(f"🏭 AIServiceFactory готова: {list(ai_factory._services.keys())}")
    
    # КРИТИЧЕСКИ ВАЖНО: Инициализируем LocaleManager ПЕРЕД созданием handlers
    initialize_locale_manager(db)
    
    # Initialize handlers
    message_handlers = MessageHandlers(config, analysis_service)
    callback_handlers = CallbackHandlers(config, analysis_service)
    document_handlers = DocumentHandler(config, analysis_service)
    
    # Initialize Firestore service
    firestore_service = get_firestore_service(db)
    
    # Initialize template management handler
    template_handler = TemplateManagementHandler(config, firestore_service)
    
    # Create dashboard conversation handler
    dashboard_conv_handler = create_dashboard_conversation_handler(config)
    
    # Create template management conversation handler
    template_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("templates", template_handler.templates_command),
            CallbackQueryHandler(template_handler.start_template_upload, pattern="^upload_template$")
        ],
        states={
            config.AWAITING_TEMPLATE_UPLOAD: [
                MessageHandler(filters.Document.ALL, template_handler.handle_template_upload),
                CommandHandler("cancel", template_handler.cancel_template_upload)
            ],
            config.AWAITING_TEMPLATE_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, template_handler.handle_template_name_and_save),
                CommandHandler("cancel", template_handler.cancel_template_upload)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", template_handler.cancel_template_upload)
        ],
        per_message=False
    )
    
    # Initialize message sender for centralized message sending
    # Example usage:
    # message_sender = MessageSender(config)
    # await message_sender.send_success_message(update, context, "Операция выполнена успешно!")
    # await message_sender.send_error_message(update, context, "Произошла ошибка при обработке")
    # await message_sender.send_temp_message(update, context, "Временное сообщение", duration=5)
    
    # Ingredient storage removed for template - not needed for basic bot functionality
    
    # Create application
    application = Application.builder().token(config.BOT_TOKEN).concurrent_updates(True).build()
    
    # Services removed for template - only basic bot functionality remains
    print("✅ Template mode: Advanced services disabled")

    # Create conversation handler with document creation workflow
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", message_handlers.start),
            CommandHandler("help", message_handlers.help_command),
            CommandHandler("dashboard", message_handlers.dashboard_command),
            CommandHandler("new_contract", document_handlers.new_contract_command),
            CommandHandler("templates", template_handler.templates_command),
            MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_text),
            MessageHandler(filters.Document.ALL, message_handlers.handle_document),
            CallbackQueryHandler(callback_handlers.handle_callback_query)
        ],
        states={
            config.AWAITING_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_text),
                MessageHandler(filters.Document.ALL, message_handlers.handle_document),
                CommandHandler("help", message_handlers.help_command),
                CommandHandler("dashboard", message_handlers.dashboard_command),
                CommandHandler("new_contract", document_handlers.new_contract_command),
                CallbackQueryHandler(callback_handlers.handle_callback_query)
            ],
            config.AWAITING_COMPANY_INFO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, document_handlers.handle_company_info),
                CommandHandler("cancel", document_handlers.cancel_document_creation)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", message_handlers.start),
            CommandHandler("help", message_handlers.help_command)
        ],
        per_message=False
    )

    # Add handlers - IMPORTANT: Order matters! More specific handlers should be added first
    application.add_handler(template_conv_handler)  # Template handler first (handles upload_template)
    application.add_handler(dashboard_conv_handler)  # Dashboard handler second
    application.add_handler(conv_handler)  # General handler last (catches everything else)
    
    # Role initialization removed for template

    # 4. Запускаем бота
    print("🚀 Бот запускается...")
    
    try:
        safe_start_bot(application)
    except KeyboardInterrupt:
        print("\n⏹️ Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        print("💡 Попробуйте:")
        print("   1. Убедиться, что не запущено других экземпляров бота")
        print("   2. Проверить интернет-соединение")
        print("   3. Перезапустить через несколько минут")


if __name__ == "__main__":
    main()
