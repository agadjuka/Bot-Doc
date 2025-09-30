#!/usr/bin/env python3
"""
Тестовый скрипт для отладки системы обработки шаблонов
"""
import asyncio
import os
from services.template_processor_service import TemplateProcessorService

async def test_template_processing():
    """Тестируем обработку шаблона с отладочными сообщениями"""
    
    # Инициализируем сервис
    service = TemplateProcessorService()
    
    # Путь к тестовому файлу (замените на реальный путь)
    test_file_path = "templates/test_template.docx"  # Замените на реальный путь
    
    if not os.path.exists(test_file_path):
        print(f"❌ Тестовый файл не найден: {test_file_path}")
        print("💡 Создайте тестовый .docx файл или укажите правильный путь")
        return
    
    try:
        # Читаем файл
        with open(test_file_path, 'rb') as f:
            file_bytes = f.read()
        
        print(f"📄 Загружен файл: {len(file_bytes)} байт")
        
        # Анализируем и подготавливаем шаблоны
        print("\n🚀 Начинаем анализ документа...")
        preview_bytes, smart_template_bytes = await service.analyze_and_prepare_templates(file_bytes)
        
        if preview_bytes and smart_template_bytes:
            print(f"\n✅ Обработка завершена успешно!")
            print(f"📊 Preview: {len(preview_bytes)} байт")
            print(f"📊 Smart template: {len(smart_template_bytes)} байт")
            
            # Сохраняем результаты для проверки
            with open("debug_preview.docx", "wb") as f:
                f.write(preview_bytes)
            print("💾 Preview сохранен как debug_preview.docx")
            
            with open("debug_smart_template.docx", "wb") as f:
                f.write(smart_template_bytes)
            print("💾 Smart template сохранен как debug_smart_template.docx")
        else:
            print("❌ Ошибка при обработке документа")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_template_processing())
