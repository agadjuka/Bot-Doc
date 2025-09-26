"""
Main entry point for the AI Bot application with webhook support for Cloud Run
Using FastAPI for better performance and modern async support
"""
import os
import asyncio
from typing import Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
from telegram import Update
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

# Инициализация клиента Firestore
# Этот код будет работать автоматически в Cloud Run
# и при локальной настройке с переменной окружения.
from google.cloud import firestore

# Инициализация клиента Firestore с обработкой ошибок
# В Cloud Run используется Application Default Credentials (ADC)
db = None
try:
    # Попробуем инициализировать Firestore
    # Получаем имя базы данных из переменных окружения
    database_name = os.getenv("FIRESTORE_DATABASE", "default")
    db = firestore.Client(database=database_name)
    print(f"✅ Firestore клиент инициализирован успешно (база: {database_name})")
except Exception as e:
    print(f"❌ Ошибка инициализации Firestore: {e}")
    print("💡 В Cloud Run используется Application Default Credentials (ADC)")
    print("💡 Firestore может быть недоступен, но бот будет работать без сохранения языков")
    db = None

# В Cloud Run переменные окружения настраиваются через консоль Google Cloud
# или через deployment конфигурацию - никакой дополнительной настройки не требуется

# КРИТИЧЕСКИ ВАЖНО: Инициализируем LocaleManager СРАЗУ после Firestore
# Это должно произойти ДО импорта handlers, чтобы избежать race condition
from config.locales.locale_manager import initialize_locale_manager
initialize_locale_manager(db)

# Role initialization will be done in initialize_bot function

# Проверяем совместимость numpy/pandas перед импортом других модулей
try:
    import numpy as np
    import pandas as pd
    print(f"✅ numpy версия: {np.__version__}")
    print(f"✅ pandas версия: {pd.__version__}")
except ImportError as e:
    print(f"❌ Ошибка импорта numpy/pandas: {e}")
    # Не прерываем запуск, если numpy/pandas недоступны
    np = None
    pd = None

# OpenCV removed for template - not needed for basic bot functionality
opencv_available = False

# Импорты с обработкой ошибок
try:
    from config.settings import BotConfig
    from config.prompts import PromptManager
    from services.ai_service import AIService, ReceiptAnalysisServiceCompat, AIServiceFactory
    from handlers.message_handlers import MessageHandlers
    from handlers.callback_handlers import CallbackHandlers
    from handlers.document_handler import DocumentHandler
    from handlers.dashboard_handler import create_dashboard_conversation_handler
    from handlers.template_management_handler import TemplateManagementHandler
    from services.firestore_service import get_firestore_service
    # IngredientStorage removed for template
    # MessageSender removed for template
    # Google Sheets handler removed for template
    print("✅ Все модули импортированы успешно")
except ImportError as e:
    print(f"❌ Ошибка импорта модулей: {e}")
    # Устанавливаем None для всех модулей
    BotConfig = None
    PromptManager = None
    AIService = None
    ReceiptAnalysisServiceCompat = None
    MessageHandlers = None
    CallbackHandlers = None
    DocumentHandler = None
    create_dashboard_conversation_handler = None
    TemplateManagementHandler = None
    get_firestore_service = None
    # IngredientStorage removed for template
    # MessageSender removed for template
    # get_google_sheets_ingredients = None  # Removed for template

# Bot configuration - будет инициализирован позже
TOKEN = None
TELEGRAM_API = None

# FastAPI app
app = FastAPI(title="AI Bot", description="Telegram Bot for receipt processing")

# Global variables
application: Optional[Application] = None
keep_alive_task_obj: Optional[asyncio.Task] = None
locale_manager_cache: Optional[object] = None

# Cleanup function removed for template - not needed for basic bot functionality

async def send_keep_alive_request() -> None:
    """Отправляет простой HTTP запрос на собственный URL для keep-alive"""
    # Получаем URL сервиса из переменных окружения
    SERVICE_URL = os.getenv("SERVICE_URL", "")
    
    if not SERVICE_URL:
        print("⚠️ SERVICE_URL не установлен, пропускаем keep-alive")
        return
    
    try:
        # Убираем trailing slash если есть
        base_url = SERVICE_URL.rstrip('/')
        
        # Пробуем разные endpoints для keep-alive
        endpoints_to_try = [
            f"{base_url}/keepalive",  # Специальный keep-alive endpoint
            f"{base_url}/",           # Health check endpoint
            f"{base_url}/health"      # Альтернативный health endpoint
        ]
        
        async with httpx.AsyncClient(timeout=5.0) as client:  # Уменьшили timeout
            for endpoint in endpoints_to_try:
                try:
                    response = await client.get(endpoint)
                    if response.status_code == 200:
                        print(f"✅ Keep-alive HTTP запрос успешен: {endpoint}")
                        return
                    else:
                        print(f"⚠️ Keep-alive HTTP запрос неуспешен: {endpoint} (HTTP {response.status_code})")
                except Exception as e:
                    print(f"⚠️ Ошибка keep-alive HTTP запроса {endpoint}: {e}")
                    continue
            
            # Если все endpoints не сработали, выводим предупреждение
            print("⚠️ Все keep-alive endpoints недоступны, но это не критично")
            
    except Exception as e:
        print(f"❌ Ошибка в send_keep_alive_request: {e}")
        # НЕ поднимаем исключение - keep-alive не должен влиять на работу бота

async def keep_alive_task() -> None:
    """Keep-alive задача для предотвращения засыпания Cloud Run - НЕЗАВИСИМАЯ ВЕРСИЯ"""
    print("💓 Keep-alive задача запущена (независимая версия)")
    
    while True:
        try:
            await asyncio.sleep(600)  # 10 minutes = 600 seconds
            
            import datetime
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"💓 Keep-alive ping: {current_time}")
            
            # Всегда пытаемся отправить HTTP запрос - никаких проверок переменных окружения
            try:
                await send_keep_alive_request()
                print("✅ Keep-alive HTTP запрос отправлен")
            except Exception as e:
                print(f"❌ Ошибка отправки keep-alive HTTP запроса: {e}")
                # Продолжаем работу даже при ошибке HTTP запроса
                
        except asyncio.CancelledError:
            print("💓 Keep-alive задача отменена")
            break
        except Exception as e:
            print(f"❌ Ошибка в keep-alive задаче: {e}")
            # Продолжаем работу даже при ошибке - keep-alive НЕ должен влиять на бота
            await asyncio.sleep(60)  # Ждем минуту перед следующей попыткой

async def start_keep_alive_task():
    """Запускает keep-alive задачу, если она еще не запущена - НЕЗАВИСИМАЯ ВЕРСИЯ"""
    global keep_alive_task_obj
    
    try:
        if keep_alive_task_obj is None or keep_alive_task_obj.done():
            keep_alive_task_obj = asyncio.create_task(keep_alive_task())
            print("✅ Keep-alive задача запущена (независимая версия)")
    except Exception as e:
        print(f"❌ Ошибка запуска keep-alive задачи: {e}")
        # НЕ поднимаем исключение - keep-alive не должен блокировать запуск бота

def get_cached_locale_manager():
    """Получает кэшированный LocaleManager для оптимизации"""
    global locale_manager_cache
    
    if locale_manager_cache is None:
        try:
            from config.locales.locale_manager import get_global_locale_manager
            locale_manager_cache = get_global_locale_manager()
        except Exception as e:
            print(f"❌ Ошибка получения LocaleManager: {e}")
            return None
    
    return locale_manager_cache

def create_application() -> Application:
    """Create and configure the Telegram application"""
    # Check if all required modules are available
    if not all([BotConfig, PromptManager, AIService, ReceiptAnalysisServiceCompat, 
                MessageHandlers, CallbackHandlers, DocumentHandler, create_dashboard_conversation_handler,
                TemplateManagementHandler, get_firestore_service]):
        raise ImportError("Required modules are not available")
    
    # Initialize configuration
    config = BotConfig()
    prompt_manager = PromptManager()
    
    # Initialize AI Service Factory for dual model support
    ai_factory = AIServiceFactory(config, prompt_manager)
    
    # Get default AI service (Pro model)
    ai_service = ai_factory.get_default_service()
    analysis_service = ReceiptAnalysisServiceCompat(ai_service, ai_factory)
    
    print(f"🤖 AI Service инициализирован с моделью: {ai_service.get_current_model_info()['name']}")
    print(f"🏭 AIServiceFactory готова для переключения между моделями: {list(ai_factory._services.keys())}")
    
    # LocaleManager уже инициализирован глобально с Firestore instance
    
    # Initialize handlers AFTER LocaleManager is initialized
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
    
    # Ingredient storage removed for template - not needed for basic bot functionality
    
    # Create application
    application = Application.builder().token(TOKEN).concurrent_updates(True).build()
    
    
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
            CallbackQueryHandler(callback_handlers.handle_callback_query)
        ],
        states={
            config.AWAITING_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_text),
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

    # Add handlers
    application.add_handler(conv_handler)
    application.add_handler(dashboard_conv_handler)
    application.add_handler(template_conv_handler)
    
    # Add basic command handlers for template
    application.add_handler(CommandHandler("start", message_handlers.start))
    application.add_handler(CommandHandler("help", message_handlers.help_command))
    
    return application

async def initialize_bot():
    """Initialize the bot application and start background tasks for Cloud Run"""
    global application, TOKEN, TELEGRAM_API
    
    # Проверяем, не инициализирован ли уже бот
    if application is not None:
        print("⚠️ Бот уже инициализирован, пропускаем повторную инициализацию")
        return
    
    print("🚀 Инициализация бота для Cloud Run...")
    
    # Debug: Print environment variables (only sensitive ones)
    print("🔍 Debug: Environment variables:")
    for key, value in os.environ.items():
        if any(keyword in key.upper() for keyword in ["TOKEN", "PROJECT", "WEBHOOK", "GOOGLE", "CREDENTIALS"]):
            print(f"  {key}: {'*' * len(value) if value else 'NOT SET'}")
    
    # Check if BOT_TOKEN is available
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        print("❌ BOT_TOKEN не найден в переменных окружения")
        print("💡 Установите переменную окружения BOT_TOKEN в Cloud Run")
        return
    
    TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"
    print("✅ BOT_TOKEN найден")
    
    # Create application
    print("🔧 Создаем Telegram application...")
    try:
        application = create_application()
        print(f"✅ Application создан: {application}")
    except Exception as e:
        print(f"❌ Ошибка создания application: {e}")
        return
    
    # Start keep-alive task for Cloud Run
    try:
        await start_keep_alive_task()
        print("✅ Keep-alive задача запущена")
    except Exception as e:
        print(f"⚠️ Keep-alive задача не запустилась: {e}")
        # НЕ прерываем инициализацию - keep-alive не критичен
    
    # Initialize the application
    print("🔧 Инициализируем Telegram application...")
    try:
        await application.initialize()
        print("✅ Telegram application инициализирован")
    except Exception as e:
        print(f"❌ Ошибка инициализации application: {e}")
        return
    
    # Проверяем, что LocaleManager работает
    try:
        from config.locales.locale_manager import get_global_locale_manager
        lm = get_global_locale_manager()
        print(f"✅ LocaleManager проверен: {lm}")
        if hasattr(lm, 'language_service') and lm.language_service and lm.language_service.db:
            print("✅ LocaleManager подключен к Firestore")
        else:
            print("⚠️ LocaleManager НЕ подключен к Firestore")
    except Exception as e:
        print(f"❌ Ошибка проверки LocaleManager: {e}")
    
    print("🚀 Бот инициализирован для webhook режима в Cloud Run")

@app.on_event("startup")
async def startup_event():
    """Initialize bot on startup"""
    print("🚀 Запуск приложения...")
    
    # Запускаем keep-alive задачу в фоне - НЕ блокируем запуск бота
    try:
        await start_keep_alive_task()
    except Exception as e:
        print(f"⚠️ Keep-alive задача не запустилась: {e}")
        # НЕ прерываем запуск - keep-alive не критичен
    
    try:
        await initialize_bot()
    except Exception as e:
        print(f"❌ Ошибка при инициализации бота: {e}")
        import traceback
        traceback.print_exc()
        # Не прерываем запуск приложения, если бот не может инициализироваться

@app.get("/")
async def health_check():
    """Health check endpoint for Cloud Run - OPTIMIZED"""
    return {
        "status": "ok", 
        "message": "AI Bot is running",
        "application_initialized": application is not None,
        "firestore_connected": db is not None,
        "keep_alive_running": keep_alive_task_obj is not None and not keep_alive_task_obj.done()
    }

@app.post("/set_webhook")
async def set_webhook(request: Request):
    """Manual webhook setup endpoint"""
    try:
        data = await request.json()
        webhook_url = data.get("webhook_url")
        if not webhook_url:
            raise HTTPException(status_code=400, detail="webhook_url is required")
        
        if not application:
            raise HTTPException(status_code=500, detail="Bot not initialized")
        
        result = await application.bot.set_webhook(
            url=f"{webhook_url}/webhook",
            drop_pending_updates=True
        )
        
        return {
            "status": "success", 
            "webhook_url": f"{webhook_url}/webhook",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_webhook")
async def get_webhook():
    """Get current webhook info"""
    try:
        if not application:
            raise HTTPException(status_code=500, detail="Bot not initialized")
        
        webhook_info = await application.bot.get_webhook_info()
        
        return {
            "webhook_info": webhook_info.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debug")
async def debug_info():
    """Debug information endpoint"""
    from config.locales.locale_manager import get_global_locale_manager
    
    locale_manager_status = "Not initialized"
    try:
        lm = get_global_locale_manager()
        locale_manager_status = "Initialized"
        if hasattr(lm, 'language_service') and lm.language_service:
            if lm.language_service.db:
                locale_manager_status += " with Firestore"
            else:
                locale_manager_status += " without Firestore"
    except Exception as e:
        locale_manager_status = f"Error: {str(e)}"
    
    return {
        "application_initialized": application is not None,
        "firestore_connected": db is not None,
        "bot_token_set": TOKEN is not None,
        "locale_manager_status": locale_manager_status,
        "keep_alive_active": True,  # Keep-alive всегда активен, если сервер работает
        "environment_vars": {
            "BOT_TOKEN": "***" if os.getenv("BOT_TOKEN") else "NOT SET",
            "PROJECT_ID": "***" if os.getenv("PROJECT_ID") else "NOT SET",
            "WEBHOOK_URL": "***" if os.getenv("WEBHOOK_URL") else "NOT SET",
            "GOOGLE_APPLICATION_CREDENTIALS_JSON": "***" if os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON") else "NOT SET"
        },
        "template_mode": True
    }

@app.get("/keepalive")
async def keepalive_check():
    """Keep-alive check endpoint - OPTIMIZED"""
    import datetime
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return {
        "status": "alive",
        "timestamp": current_time,
        "application_initialized": application is not None,
        "keep_alive_running": keep_alive_task_obj is not None and not keep_alive_task_obj.done(),
        "message": "Keep-alive check successful"
    }

@app.get("/status")
async def cloud_status():
    """Статус облачной версии бота для Cloud Run"""
    from config.locales.locale_manager import get_global_locale_manager
    
    status = {
        "version": "cloud",
        "environment": "Cloud Run",
        "protocol": "webhook",
        "components": {
            "application_initialized": application is not None,
            "firestore_connected": db is not None,
            "keep_alive_running": keep_alive_task_obj is not None and not keep_alive_task_obj.done(),
            "locale_manager": False,
            "ai_service": False,
            "handlers": False
        },
        "status": "checking"
    }
    
    # Проверяем LocaleManager
    try:
        lm = get_global_locale_manager()
        if lm:
            status["components"]["locale_manager"] = True
    except Exception as e:
        print(f"⚠️ LocaleManager недоступен: {e}")
    
    # Проверяем AI Service
    try:
        if all([BotConfig, PromptManager, AIService, ReceiptAnalysisServiceCompat]):
            status["components"]["ai_service"] = True
    except Exception as e:
        print(f"⚠️ AI Service недоступен: {e}")
    
    # Проверяем Handlers
    try:
        if all([MessageHandlers, CallbackHandlers, DocumentHandler]):
            status["components"]["handlers"] = True
    except Exception as e:
        print(f"⚠️ Handlers недоступны: {e}")
    
    # Определяем общий статус
    critical_components = ["application_initialized", "handlers"]
    if all(status["components"][component] for component in critical_components):
        status["status"] = "operational"
    else:
        status["status"] = "degraded"
    
    return status


@app.post("/webhook")
async def webhook(request: Request):
    """Webhook endpoint for Telegram updates - ULTRA-OPTIMIZED VERSION"""
    try:
        # Get the update from Telegram
        update_data = await request.json()
        
        if not update_data:
            return {"ok": True}
        
        if not application:
            return {"ok": True, "error": "Bot not initialized"}
        
        # Process update normally for template
        try:
            update = Update.de_json(update_data, application.bot)
            
            if not update:
                return {"ok": True}
            
            # Process all updates normally
            await application.process_update(update)
            return {"ok": True}
            
        except Exception as e:
            print(f"❌ Ошибка при обработке update: {e}")
            return {"ok": True, "error": f"Processing error: {str(e)}"}
        
    except Exception as e:
        print(f"❌ Ошибка при обработке webhook: {e}")
        return {"ok": True, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)