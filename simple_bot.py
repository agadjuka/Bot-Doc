#!/usr/bin/env python3
"""
Simple bot without AI service - just basic functionality
"""
import os
import json
import asyncio
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
)
from telegram.error import Conflict, NetworkError

def setup_environment():
    """Setup environment from JSON file"""
    current_dir = os.getcwd()
    json_file = os.path.join(current_dir, 'google-cloud-credentials.json')
    
    if not os.path.exists(json_file):
        print(f"❌ JSON file not found: {json_file}")
        return False
    
    # Set environment variables
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = json_file
    os.environ['PROJECT_ID'] = 'bot-doc-473208'
    os.environ['GOOGLE_CLOUD_LOCATION'] = 'asia-southeast1'
    os.environ['FIRESTORE_DATABASE'] = 'default'
    
    print("✅ Environment configured from JSON")
    return True

async def start_command(update, context):
    """Handle /start command"""
    await update.message.reply_text(
        "🤖 **Добро пожаловать в Bot Doc!**\n\n"
        "Доступные команды:\n"
        "/start - Запуск бота\n"
        "/help - Справка\n"
        "/new_contract - Создание нового документа",
        parse_mode='HTML'
    )

async def help_command(update, context):
    """Handle /help command"""
    await update.message.reply_text(
        "📋 **Справка по боту**\n\n"
        "Этот бот поможет вам:\n"
        "• Создавать документы\n"
        "• Обрабатывать информацию о компаниях\n\n"
        "Команды:\n"
        "/start - Запуск бота\n"
        "/help - Эта справка\n"
        "/new_contract - Создать новый документ",
        parse_mode='HTML'
    )

async def new_contract_command(update, context):
    """Handle /new_contract command"""
    await update.message.reply_text(
        "📄 **Создание нового документа**\n\n"
        "Пожалуйста, скопируйте и пришлите мне реквизиты компании "
        "(карточку предприятия) одним сообщением. Я проанализирую их "
        "и подготовлю документ.",
        parse_mode='HTML'
    )

async def handle_text(update, context):
    """Handle text messages"""
    user_text = update.message.text
    
    # Simple response
    await update.message.reply_text(
        f"✅ Получено сообщение: {user_text[:100]}...\n\n"
        "Используйте /new_contract для создания документа.",
        parse_mode='HTML'
    )

def safe_start_bot(application: Application, max_retries: int = 3) -> None:
    """Safe bot startup with conflict handling"""
    for attempt in range(max_retries):
        try:
            print(f"Попытка запуска бота #{attempt + 1}...")
            
            # Reset webhook
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(application.bot.delete_webhook(drop_pending_updates=True))
                print("✅ Webhook сброшен")
            except Exception as e:
                print(f"⚠️ Предупреждение при сбросе webhook: {e}")
            
            # Start bot
            application.run_polling()
            break
            
        except Conflict as e:
            print(f"❌ Конфликт (попытка {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                import time
                wait_time = (attempt + 1) * 5
                print(f"⏳ Ожидание {wait_time} секунд...")
                time.sleep(wait_time)
            else:
                print("❌ Максимальное количество попыток исчерпано")
                raise
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            raise

def main():
    """Main function"""
    print("🚀 Запуск простого бота...")
    
    # Setup environment
    if not setup_environment():
        return
    
    # Check BOT_TOKEN
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        print("❌ BOT_TOKEN не установлен!")
        print("   Установите: $env:BOT_TOKEN = 'ваш_токен'")
        return
    
    print("✅ BOT_TOKEN найден")
    
    # Create application
    application = Application.builder().token(bot_token).concurrent_updates(True).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("new_contract", new_contract_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("✅ Обработчики добавлены")
    print("🤖 Бот запускается...")
    
    try:
        safe_start_bot(application)
    except KeyboardInterrupt:
        print("\n⏹️ Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()
