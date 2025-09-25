#!/usr/bin/env python3
"""
Пример интеграции FirestoreService с Telegram ботом
Показывает, как использовать сервис для управления шаблонами документов
"""
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from services.firestore_service import get_firestore_service

class TemplateManager:
    """Менеджер шаблонов для интеграции с ботом"""
    
    def __init__(self):
        self.firestore_service = get_firestore_service()
    
    async def handle_document_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик загрузки документа как шаблона"""
        user_id = update.effective_user.id
        document = update.message.document
        
        # Проверяем, что это .docx файл
        if document.mime_type != 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            await update.message.reply_text(
                "❌ Пожалуйста, загрузите файл в формате .docx"
            )
            return
        
        # Получаем название файла
        template_name = document.file_name or f"Шаблон_{document.file_id[:8]}"
        
        # Сохраняем шаблон в Firestore
        success = await self.firestore_service.add_template(
            user_id=user_id,
            template_name=template_name,
            file_id=document.file_id,
            file_type='docx'
        )
        
        if success:
            await update.message.reply_text(
                f"✅ Шаблон '{template_name}' успешно сохранен!\n"
                f"Теперь вы можете использовать его для создания документов."
            )
        else:
            await update.message.reply_text(
                "❌ Ошибка при сохранении шаблона. Попробуйте еще раз."
            )
    
    async def list_user_templates(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать список шаблонов пользователя"""
        user_id = update.effective_user.id
        
        templates = await self.firestore_service.get_templates(user_id)
        
        if not templates:
            await update.message.reply_text(
                "📝 У вас пока нет сохраненных шаблонов.\n"
                "Загрузите .docx файл, чтобы создать первый шаблон."
            )
            return
        
        # Формируем список шаблонов
        message = "📋 Ваши шаблоны:\n\n"
        for i, template in enumerate(templates, 1):
            created_at = template.get('created_at', 'Неизвестно')
            if hasattr(created_at, 'strftime'):
                created_at = created_at.strftime('%d.%m.%Y %H:%M')
            
            message += f"{i}. **{template['template_name']}**\n"
            message += f"   📅 Создан: {created_at}\n"
            message += f"   🆔 ID: `{template['template_doc_id']}`\n\n"
        
        message += "💡 Используйте ID шаблона для создания документов"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def use_template(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Использовать шаблон для создания документа"""
        user_id = update.effective_user.id
        template_doc_id = context.args[0] if context.args else None
        
        if not template_doc_id:
            await update.message.reply_text(
                "❌ Укажите ID шаблона.\n"
                "Пример: /use_template abc123def456"
            )
            return
        
        # Получаем информацию о шаблоне
        template_info = await self.firestore_service.get_template_info(user_id, template_doc_id)
        
        if not template_info:
            await update.message.reply_text(
                "❌ Шаблон не найден. Проверьте ID шаблона."
            )
            return
        
        # Здесь можно добавить логику создания документа на основе шаблона
        await update.message.reply_text(
            f"✅ Используем шаблон: **{template_info['template_name']}**\n"
            f"📁 File ID: `{template_info['file_id']}`\n\n"
            f"💡 В будущем здесь будет создание документа на основе шаблона",
            parse_mode='Markdown'
        )
    
    async def delete_template(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Удалить шаблон"""
        user_id = update.effective_user.id
        template_doc_id = context.args[0] if context.args else None
        
        if not template_doc_id:
            await update.message.reply_text(
                "❌ Укажите ID шаблона для удаления.\n"
                "Пример: /delete_template abc123def456"
            )
            return
        
        # Получаем информацию о шаблоне перед удалением
        template_info = await self.firestore_service.get_template_info(user_id, template_doc_id)
        
        if not template_info:
            await update.message.reply_text(
                "❌ Шаблон не найден. Проверьте ID шаблона."
            )
            return
        
        # Удаляем шаблон
        success = await self.firestore_service.delete_template(user_id, template_doc_id)
        
        if success:
            await update.message.reply_text(
                f"✅ Шаблон '{template_info['template_name']}' успешно удален."
            )
        else:
            await update.message.reply_text(
                "❌ Ошибка при удалении шаблона. Попробуйте еще раз."
            )
    
    async def rename_template(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Переименовать шаблон"""
        user_id = update.effective_user.id
        
        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ Укажите ID шаблона и новое название.\n"
                "Пример: /rename_template abc123def456 Новое название"
            )
            return
        
        template_doc_id = context.args[0]
        new_name = ' '.join(context.args[1:])
        
        # Переименовываем шаблон
        success = await self.firestore_service.update_template_name(
            user_id, template_doc_id, new_name
        )
        
        if success:
            await update.message.reply_text(
                f"✅ Шаблон успешно переименован в '{new_name}'."
            )
        else:
            await update.message.reply_text(
                "❌ Ошибка при переименовании шаблона. Проверьте ID шаблона."
            )

# Пример использования в обработчиках команд
async def setup_template_handlers(application):
    """Настройка обработчиков команд для работы с шаблонами"""
    template_manager = TemplateManager()
    
    # Добавляем обработчики команд
    from telegram.ext import CommandHandler, MessageHandler, filters
    
    application.add_handler(CommandHandler("templates", template_manager.list_user_templates))
    application.add_handler(CommandHandler("use_template", template_manager.use_template))
    application.add_handler(CommandHandler("delete_template", template_manager.delete_template))
    application.add_handler(CommandHandler("rename_template", template_manager.rename_template))
    
    # Обработчик загрузки документов
    application.add_handler(MessageHandler(
        filters.Document.MimeType("application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        template_manager.handle_document_upload
    ))

# Пример команды помощи
HELP_TEXT = """
📋 **Управление шаблонами документов**

**Команды:**
• `/templates` - Показать список ваших шаблонов
• `/use_template <ID>` - Использовать шаблон для создания документа
• `/delete_template <ID>` - Удалить шаблон
• `/rename_template <ID> <новое_название>` - Переименовать шаблон

**Загрузка шаблонов:**
Просто отправьте .docx файл боту, и он автоматически сохранится как шаблон.

**Примеры:**
• `/templates` - посмотреть все шаблоны
• `/use_template abc123def456` - использовать шаблон
• `/delete_template abc123def456` - удалить шаблон
• `/rename_template abc123def456 Мой новый шаблон` - переименовать
"""

if __name__ == "__main__":
    print("📋 Пример интеграции FirestoreService с Telegram ботом")
    print("💡 Этот файл показывает, как использовать сервис в реальном боте")
    print("\n🔧 Для тестирования запустите:")
    print("python test_firestore_service.py")
